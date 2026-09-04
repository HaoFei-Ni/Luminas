"""lumina-eng-skill L4 性能测试协议（最高档，固定口径）.

test-matrix：2 warmup + 5 timed；报告 mean±std；禁止 best-of-N。
回归：相对基线延迟升高不得超过 ``max_ratio``（默认 2%）。
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# 最高档固定；禁止由调用方改小以“刷过”门禁。
WARMUP_RUNS = 2
TIMED_RUNS = 5
DEFAULT_MAX_REGRESSION = 0.02


@dataclass(frozen=True)
class TimingResult:
    """Timed-run statistics in seconds (warmup discarded)."""

    samples_s: tuple[float, ...]
    mean_s: float
    std_s: float


def time_callable(
    fn: Callable[[], None],
    *,
    warmup: int = WARMUP_RUNS,
    timed: int = TIMED_RUNS,
) -> TimingResult:
    """Run ``fn`` with fixed warmup/timed counts; return mean±std of timed samples."""
    if warmup != WARMUP_RUNS or timed != TIMED_RUNS:
        raise ValueError(f"最高档协议固定为 warmup={WARMUP_RUNS}, timed={TIMED_RUNS}")
    # 单遍：warmup 丢弃，避免冷启动污染计时。
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    # 单遍：固定 5 次全计时，避免 best-of-N 粉饰回归。
    for _ in range(timed):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    mean = sum(samples) / timed
    var = sum((item - mean) ** 2 for item in samples) / timed
    return TimingResult(samples_s=tuple(samples), mean_s=mean, std_s=math.sqrt(var))


def check_latency_regression(
    current_s: float,
    baseline_s: float,
    *,
    max_ratio: float = DEFAULT_MAX_REGRESSION,
) -> str | None:
    """Return issue text when current latency exceeds baseline by more than max_ratio."""
    if baseline_s <= 0.0:
        raise ValueError("baseline_s must be positive")
    if current_s < 0.0:
        raise ValueError("current_s must be non-negative")
    limit = baseline_s * (1.0 + max_ratio)
    if current_s <= limit:
        return None
    pct = max_ratio * 100.0
    return f"延迟回归超限：current={current_s:.6g}s baseline={baseline_s:.6g}s limit={limit:.6g}s (≤{pct:g}%)"


def interleaved_relative_score(
    calib: Callable[[], None],
    workload: Callable[[], None],
    *,
    warmup_pairs: int = 8,
    timed_pairs: int = 120,
    median_of: int = 5,
) -> float:
    """Return median(kernel/calib) from interleaved wall-time pairs (Windows-stable)."""
    # 必须先热身：冷缓存会把首比值抬高并击穿 2% 门。
    for _ in range(warmup_pairs):
        calib()
        workload()
    # 必须多次取中位：单次交错窗仍可能被调度尖峰污染。
    ratios = [_one_interleaved_ratio(calib, workload, timed_pairs) for _ in range(median_of)]
    return sorted(ratios)[len(ratios) // 2]


def _one_interleaved_ratio(
    calib: Callable[[], None],
    workload: Callable[[], None],
    timed_pairs: int,
) -> float:
    """Accumulate one interleaved calib/kernel window and return kern/calib."""
    calib_s = 0.0
    kern_s = 0.0
    # 必须同窗交替：独立两次 mean 的比值在短计时下噪声常 >> 2%。
    for _ in range(timed_pairs):
        start = time.perf_counter()
        calib()
        calib_s += time.perf_counter() - start
        start = time.perf_counter()
        workload()
        kern_s += time.perf_counter() - start
    if calib_s <= 0.0:
        raise RuntimeError("calibration mean must be positive")
    return kern_s / calib_s
