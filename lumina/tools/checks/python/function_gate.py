"""Python 函数级结构门禁：行数 / 认知·圈复杂度 / 控制嵌套 / 自递归.

从 ``ci_quality_gate`` 拆出，避免单文件函数数与 C901 超限。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.support.metrics import FunctionMetrics


def function_structure_violations(
    function_metrics: list[FunctionMetrics],
    config: dict[str, Any],
) -> list[dict[str, str]]:
    """Return violation records for every enabled per-function structure check."""
    thresholds = config["thresholds"]
    features = config["features"]
    exclusions = config["exclusions"]
    skipped = set(exclusions["function_names"])
    recursion_ok = set(exclusions.get("recursion_allowed_functions", []))
    out: list[dict[str, str]] = []
    # 单遍：跳过 exclusions.function_names（如 main），避免脚本入口误杀。
    for func in function_metrics:
        if func.name in skipped:
            continue
        out.extend(_one_function(func, features, thresholds, recursion_ok))
    return out


def _one_function(
    func: FunctionMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
    recursion_ok: set[str],
) -> list[dict[str, str]]:
    """Evaluate one function against all enabled structure thresholds."""
    target = f"{func.file_key}::{func.name}"
    out: list[dict[str, str]] = []
    _append_over(
        out,
        target,
        "函数物理行数超限",
        features["enable_function_lines_check"],
        func.lines,
        thresholds["max_function_physical_lines"],
    )
    _append_over(
        out,
        target,
        "认知复杂度超限",
        features["enable_cognitive_complexity_check"],
        func.complexity,
        thresholds["max_cognitive_complexity"],
    )
    _append_over(
        out,
        target,
        "圈复杂度超限",
        features.get("enable_cyclomatic_complexity_check", False),
        func.cyclomatic,
        thresholds.get("max_cyclomatic_complexity", 20),
    )
    _append_over(
        out,
        target,
        "控制嵌套超限",
        features.get("enable_control_nesting_check", False),
        func.control_nesting,
        thresholds.get("max_control_nesting_depth", 5),
    )
    if features.get("enable_recursion_check", True) and func.has_recursion and func.name not in recursion_ok:
        out.append(_violation(target, "函数含自递归（默认禁止）", 1, 0))
    return out


def _append_over(
    out: list[dict[str, str]],
    target: str,
    issue: str,
    enabled: bool,
    value: int | None,
    limit: int,
) -> None:
    """Append a violation when an enabled metric exceeds its limit."""
    if enabled and value is not None and value > limit:
        out.append(_violation(target, issue, value, limit))


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """Build one normalized violation record."""
    return {"target": target, "issue": issue, "current": str(current), "limit": str(limit)}
