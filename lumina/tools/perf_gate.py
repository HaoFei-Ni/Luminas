"""L4 性能门禁（最高档）：协议计时 + 相对校准基线回归.

相对分数 ``kernel_mean / calib_mean``，跨机绝对时间漂移不影响裁决；
相对分数相对仓库基线升高超过 2% 则失败。
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tools.perf_protocol import DEFAULT_MAX_REGRESSION, check_latency_regression, time_callable

if TYPE_CHECKING:
    from collections.abc import Callable

_BASELINE_SCHEMA = 1


def load_config(config_path: str = "quality-gate.toml") -> dict[str, Any]:
    """Load quality-gate.toml from the lumina working directory."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with path.open("rb") as handle:
        return dict(tomllib.load(handle))


def perf_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Run L4 benches and compare relative scores to the committed baseline."""
    standard = config.get("perf_standard", {})
    if not standard.get("enable", False):
        return []
    baseline_path = Path(standard.get("baseline_path", "tests/python/baselines/l4_perf_baseline.json"))
    max_ratio = float(standard.get("max_latency_regression", DEFAULT_MAX_REGRESSION))
    if max_ratio > DEFAULT_MAX_REGRESSION:
        return [
            _violation(
                "perf_standard",
                f"最高档 max_latency_regression 不得超过 {DEFAULT_MAX_REGRESSION}",
                max_ratio,
                DEFAULT_MAX_REGRESSION,
            )
        ]
    scores = _measure_relative_scores()
    if not baseline_path.exists():
        return [_violation(str(baseline_path), "缺少 L4 性能基线文件（最高档强制）", 0, 1)]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if int(baseline.get("schema", 0)) != _BASELINE_SCHEMA:
        return [
            _violation(
                str(baseline_path),
                "性能基线 schema 不匹配",
                int(baseline.get("schema", 0)),
                _BASELINE_SCHEMA,
            )
        ]
    return _compare_scores(scores, baseline.get("scores", {}), max_ratio)


def _measure_relative_scores() -> dict[str, float]:
    """Calibrate then bench; return relative scores (kernel/calib)."""
    calib = time_callable(_make_calib())
    if calib.mean_s <= 0.0:
        raise RuntimeError("calibration mean must be positive")
    scores: dict[str, float] = {}
    # 单遍：每个固定 workload 一份相对分数，避免把校准自身再当 bench。
    for name, workload in _bench_workloads().items():
        timed = time_callable(workload)
        scores[name] = timed.mean_s / calib.mean_s
    return scores


def _make_calib() -> Callable[[], None]:
    """Build CPU calibration workload (fixed-size float accumulate)."""

    def run() -> None:
        total = 0.0
        # 有限长度：校准规模固定，避免跨跑漂移。
        for index in range(50_000):
            total += float(index % 97) * 1.000001
        if total < 0.0:
            raise RuntimeError("unreachable")

    return run


def _bench_workloads() -> dict[str, Callable[[], None]]:
    """Always-on CPU benches used for regression scores."""
    return {"dense_saxpy_like": _make_saxpy()}


def _make_saxpy() -> Callable[[], None]:
    """Build dense axpy-like workload for hot-path style regression."""
    size = 200_000
    xs = [float(index % 13) for index in range(size)]
    ys = [float(index % 17) for index in range(size)]

    def run() -> None:
        alpha = 1.000001
        # 有限长度：固定 n，避免动态分配干扰计时。
        for index in range(size):
            ys[index] = alpha * xs[index] + ys[index]

    return run


def _compare_scores(
    current: dict[str, float],
    baseline: dict[str, float],
    max_ratio: float,
) -> list[dict[str, str]]:
    """Compare each bench score to baseline with latency-style 2% cap."""
    out: list[dict[str, str]] = []
    # 单遍：基线键必须齐全，禁止静默少跑。
    for name, base in baseline.items():
        if name not in current:
            out.append(_violation(name, "缺少对应 L4 计分结果", 0, 1))
            continue
        issue = check_latency_regression(current[name], float(base), max_ratio=max_ratio)
        if issue:
            out.append(_violation(name, issue, current[name], float(base) * (1.0 + max_ratio)))
    extras = [name for name in current if name not in baseline]
    out.extend(_violation(name, "出现未登记的 L4 bench（须写入基线）", 1, 0) for name in extras)
    return out


def _violation(target: str, issue: str, current: float | int, limit: float | int) -> dict[str, str]:
    """Normalized violation record."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


def main() -> int:
    """Run L4 perf gate and print a compact summary."""
    config = load_config()
    if not config.get("perf_standard", {}).get("enable", False):
        print("[INFO] perf_standard 未启用，跳过性能门禁")
        return 0
    try:
        violations = perf_violations(config)
    except Exception as exc:  # noqa: BLE001 — 门禁入口需把协议错误打成失败
        print(f"❌ [PERF-GATE-FAIL] {exc}")
        return 1
    print(f"[INFO] 性能扫描违规 {len(violations)}")
    # 单遍：逐条输出便于 CI 定位。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print("❌ [PERF-GATE-FAIL] L4 性能门禁未通过")
        return 1
    print("✅ [PERF-GATE-PASS] L4 性能门禁通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
