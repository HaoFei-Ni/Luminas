"""Unit tests for lumina-eng-skill L4 benchmark protocol (highest tier)."""

from __future__ import annotations

import pytest

from tools.perf_protocol import (
    TIMED_RUNS,
    WARMUP_RUNS,
    check_latency_regression,
    time_callable,
)


def test_protocol_constants_are_highest_tier() -> None:
    """L4 protocol is fixed at 2 warmup + 5 timed (test-matrix)."""
    assert WARMUP_RUNS == 2
    assert TIMED_RUNS == 5


def test_time_callable_discards_warmup_and_keeps_five() -> None:
    """Warmup samples must not enter the timed series."""
    counter = {"n": 0}

    def stub() -> None:
        counter["n"] += 1

    result = time_callable(stub)
    assert counter["n"] == WARMUP_RUNS + TIMED_RUNS
    assert len(result.samples_s) == TIMED_RUNS
    assert result.mean_s >= 0.0
    assert result.std_s >= 0.0


def test_latency_regression_rejects_over_two_percent() -> None:
    """Latency increase beyond 2% vs baseline is a hard fail."""
    assert check_latency_regression(current_s=1.02, baseline_s=1.0, max_ratio=0.02) is None
    issue = check_latency_regression(current_s=1.03, baseline_s=1.0, max_ratio=0.02)
    assert issue is not None
    assert "2%" in issue or "0.02" in issue or "回归" in issue


def test_latency_regression_rejects_non_positive_baseline() -> None:
    """Baseline must be positive; zero/negative is configuration error."""
    with pytest.raises(ValueError):
        check_latency_regression(current_s=1.0, baseline_s=0.0, max_ratio=0.02)
