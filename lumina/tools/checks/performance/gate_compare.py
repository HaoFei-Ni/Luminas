"""L4 perf gate score comparison helpers (split from gate.py for complexity budget)."""

from __future__ import annotations

from typing import Any

from tools.checks.performance.protocol import check_latency_regression


def violation(target: str, issue: str, current: float | int, limit: float | int) -> dict[str, str]:
    """Normalized violation record."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


def missing_required_violations(
    scores: dict[str, float],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    """Fail when a configured bench key is absent from measured scores."""
    required = [str(item) for item in standard.get("required_score_keys", [])]
    return [
        violation(
            name,
            "缺少产品 L4 工作负载（请 uv run python -m tools.run_build 并保证 pytest 能 import 扩展）",
            0,
            1,
        )
        for name in required  # 必须缺键即失败：避免扩展未构建时静默空跑
        if name not in scores
    ]


def compare_scores(
    current: dict[str, float],
    baseline: dict[str, float],
    max_ratio: float,
) -> list[dict[str, str]]:
    """Compare each bench score to baseline with latency-style regression cap."""
    out: list[dict[str, str]] = []
    # 必须单遍基线键：禁止静默少跑或未登记 bench。
    for name, base in baseline.items():
        entry = _baseline_entry_violation(name, current, float(base), max_ratio)
        if entry is not None:
            out.append(entry)
    out.extend(_extra_bench_violations(current, baseline))
    return out


def _baseline_entry_violation(
    name: str,
    current: dict[str, float],
    base: float,
    max_ratio: float,
) -> dict[str, str] | None:
    """Return a violation when ``name`` is missing or regressed vs baseline."""
    if name not in current:
        return violation(name, "缺少对应 L4 计分结果", 0, 1)
    issue = check_latency_regression(current[name], base, max_ratio=max_ratio)
    if not issue:
        return None
    return violation(name, issue, current[name], base * (1.0 + max_ratio))


def _extra_bench_violations(
    current: dict[str, float],
    baseline: dict[str, float],
) -> list[dict[str, str]]:
    """Flag benches present in the run but absent from the committed baseline."""
    extras = [name for name in current if name not in baseline]
    return [violation(name, "出现未登记的 L4 bench（须写入基线）", 1, 0) for name in extras]
