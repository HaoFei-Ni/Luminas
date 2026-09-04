"""L4 performance workloads used by ``performance.gate`` relative scoring."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import numpy as np

from tools.support.cache import lumina_root

if TYPE_CHECKING:
    from collections.abc import Callable

# 单次向量化须落在数毫秒以上，供 gate 交错累加；禁止 Python 循环校准。
_CALIB_N = 4_194_304
_KV_REPEAT = 262_144


def _ensure_native_on_path() -> None:
    """Prepend CMake wrapper build dir so ``_luma_native`` is importable outside pytest."""
    wrapper = lumina_root().parent / "outputs" / "build" / "lumina" / "wrapper"
    if not wrapper.is_dir():
        return
    path = str(wrapper.resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


def make_calib() -> Callable[[], None]:
    """Build numpy calibration workload (fixed-size float accumulate)."""
    payload = np.arange(_CALIB_N, dtype=np.float64)

    def run() -> None:
        # 向量化校准：与 C 扩展同属原生热路径。
        total = float(np.sum(payload * 1.000001))
        if total < 0.0:
            raise RuntimeError("unreachable")

    return run


def make_kv_roundtrip() -> Callable[[], None]:
    """Product Enc/Dec roundtrip on a fixed compressible float32 vector."""
    _ensure_native_on_path()
    import _luma_native as luma_native

    x = np.repeat(np.array([1.0, -2.0, 0.5], dtype=np.float32), _KV_REPEAT)
    n = int(x.size)

    def run() -> None:
        enc = luma_native.luma_kv_encode(x)
        dec = luma_native.luma_kv_decode(enc, n)
        if dec.shape[0] != x.shape[0]:
            raise RuntimeError("kv roundtrip size mismatch")

    return run


def bench_workloads() -> dict[str, Callable[[], None]]:
    """Always-on benches used for regression scores (product path preferred)."""
    try:
        return {"luma_kv_encode_decode_f32": make_kv_roundtrip()}
    except ImportError:
        # 无扩展时不伪造 saxpy 顶替：门禁侧将报缺分数键。
        return {}
