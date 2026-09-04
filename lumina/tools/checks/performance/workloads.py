"""L4 performance workloads used by ``perf_gate`` relative scoring."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def make_calib() -> Callable[[], None]:
    """Build CPU calibration workload (fixed-size float accumulate)."""

    def run() -> None:
        total = 0.0
        # 有限长度：校准规模固定，避免跨跑漂移。
        for index in range(50_000):
            total += float(index % 97) * 1.000001
        if total < 0.0:
            raise RuntimeError("unreachable")

    return run


def make_saxpy() -> Callable[[], None]:
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


def bench_workloads() -> dict[str, Callable[[], None]]:
    """Always-on CPU benches used for regression scores."""
    return {"dense_saxpy_like": make_saxpy()}
