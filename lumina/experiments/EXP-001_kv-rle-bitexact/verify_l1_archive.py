"""Archive Level-1 numeric gate for bit-exact KV RLE (paper L1).

Writes ``artifacts/l1_error_hist.json`` under this EXP directory.
Requires built ``_luma_native`` on ``sys.path`` (``tools.run_build``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_WRAPPER = _ROOT.parent / "outputs" / "build" / "lumina" / "wrapper"
if _WRAPPER.is_dir():
    sys.path.insert(0, str(_WRAPPER.resolve()))

import _luma_native as luma  # noqa: E402

_L1_PASS_RATE = 0.999
_SIZES = (0, 1, 64, 4096, 65536)


def _ulp2_limit(ref64: np.ndarray) -> np.ndarray:
    scale = np.maximum(1.0, np.abs(ref64))
    return (2.0 * np.finfo(np.float32).eps) * scale


def _sample_vector(rng: np.random.Generator, n: int) -> np.ndarray:
    """Build a compressible float32 vector of length ``n`` (empty when n==0)."""
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    x = rng.standard_normal(n, dtype=np.float32)
    return np.repeat(x[: max(1, n // 8)], 8)[:n].astype(np.float32)


def _accumulate_roundtrip(
    x: np.ndarray,
    total: int,
    passed: int,
    log_abs: list[float],
) -> tuple[int, int]:
    """Encode/decode one vector and accumulate L1 counters."""
    enc = np.asarray(luma.luma_kv_encode(x))
    dec = np.asarray(luma.luma_kv_decode(enc, int(x.size)))
    ref64 = x.astype(np.float64)
    err = np.abs(dec.astype(np.float64) - ref64)
    ok = np.isfinite(dec) & (err <= _ulp2_limit(ref64))
    total += int(x.size)
    passed += int(np.count_nonzero(ok))
    finite_err = err[np.isfinite(err) & (err > 0)]
    if finite_err.size:
        log_abs.extend(np.log10(finite_err).tolist())
    return total, passed


def _histogram(log_abs: list[float]) -> tuple[np.ndarray, np.ndarray]:
    if not log_abs:
        return np.zeros(0), np.zeros(1)
    return np.histogram(np.asarray(log_abs, dtype=np.float64), bins=20)


def _write_archive(payload: dict[str, Any]) -> Path:
    out_dir = Path(__file__).resolve().parent / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "l1_error_hist.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    """Run large-n roundtrips and archive pass rate + log-abs error histogram."""
    rng = np.random.default_rng(20240904)
    total = 0
    passed = 0
    log_abs: list[float] = []
    # 必须覆盖空/单/中/大：论文 L1 人口规则禁止只测玩具向量。
    for n in _SIZES:
        total, passed = _accumulate_roundtrip(_sample_vector(rng, n), total, passed, log_abs)
    rate = 1.0 if total == 0 else passed / total
    hist, edges = _histogram(log_abs)
    payload = {
        "method": "KV-ENC-CANDIDATE-1",
        "total_elements": total,
        "passed_elements": passed,
        "pass_rate": rate,
        "l1_threshold": _L1_PASS_RATE,
        "verdict": "PASS" if rate >= _L1_PASS_RATE else "FAIL",
        "log10_abs_err_hist": {"counts": hist.tolist(), "bin_edges": edges.tolist()},
    }
    path = _write_archive(payload)
    print(json.dumps({"verdict": payload["verdict"], "pass_rate": rate, "path": str(path)}, ensure_ascii=False))
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
