"""C 函数级结构门禁：尺寸 / 循环 / 嵌套 / 递归 / 文档 / 行内复杂注释.

从 ``c_quality_gate`` 拆出，用表驱动压低单函数检查复杂度。
"""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.checks.native.metrics import CFunctionMetrics

_Check = tuple[bool, bool, str, int, int]


def function_structure_violations(
    functions: list[CFunctionMetrics],
    config: dict[str, Any],
    features: dict[str, Any],
) -> list[dict[str, str]]:
    """逐函数跑尺寸/循环/嵌套/递归/文档/行内复杂注释检查."""
    thresholds = config["c_thresholds"]
    exclusions = config.get("c_exclusions", {})
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for func in functions:
        violations.extend(_one_function(func, features, thresholds, exclusions))
    return violations


def _one_function(
    func: CFunctionMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
    exclusions: dict[str, Any],
) -> list[dict[str, str]]:
    """单函数全部启用项；白名单不放行嵌套与行内复杂注释."""
    target = f"{func.file_key}::{func.name}"
    out: list[dict[str, str]] = []
    checks = _structure_checks(func, features, thresholds, exclusions)
    # 单遍：只追加超限项，避免把通过项写入报告。
    for enabled, over, issue, current, limit in checks:
        if enabled and over:
            out.append(_violation(target, issue, current, limit))
    return out


def _structure_checks(
    func: CFunctionMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
    exclusions: dict[str, Any],
) -> list[_Check]:
    """Build enabled/over/issue tuples for one function."""
    return [
        *_size_loop_checks(func, features, thresholds, exclusions),
        *_doc_inline_checks(func, features, exclusions),
    ]


def _size_loop_checks(
    func: CFunctionMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
    exclusions: dict[str, Any],
) -> list[_Check]:
    """Size / loop-count / nesting checks for one function."""
    allowed = _loops_allowed(func, exclusions)
    loop_limit = int(thresholds.get("max_loop_count_per_function", 0))
    nest_limit = int(thresholds["max_loop_nesting_depth"])
    max_lines = int(thresholds["max_function_physical_lines"])
    return [
        (features["enable_function_lines_check"], func.lines > max_lines, "C函数物理行数超限", func.lines, max_lines),
        (
            features.get("enable_loop_check", True),
            (not allowed) and func.loop_count > loop_limit,
            "C函数含循环（默认禁止）",
            func.loop_count,
            loop_limit,
        ),
        (
            features.get("enable_loop_nesting_check", True),
            func.loop_nesting > nest_limit,
            "C函数循环嵌套超限（禁止双层及以上）",
            func.loop_nesting,
            nest_limit,
        ),
    ]


def _doc_inline_checks(
    func: CFunctionMetrics,
    features: dict[str, Any],
    exclusions: dict[str, Any],
) -> list[_Check]:
    """Recursion / doc / inline-complex checks for one function."""
    recur_ok = set(exclusions.get("recursion_allowed_functions", []))
    doc_ok = set(exclusions.get("doc_comment_exempt_functions", []))
    why = features.get("enable_why_semantics", False)
    inline_issue = "C复杂语句缺少why行内注释" if why else "C复杂语句缺少行内注释"
    return [
        (
            features.get("enable_recursion_check", True),
            func.has_recursion and func.name not in recur_ok,
            "C函数含自递归（默认禁止）",
            1,
            0,
        ),
        (
            features.get("enable_function_doc_check", True),
            (not func.has_doc_comment) and func.name not in doc_ok,
            "C函数缺少前置文档注释",
            0,
            1,
        ),
        (
            features.get("enable_inline_complex_check", False),
            func.uncommented_complex > 0,
            inline_issue,
            func.uncommented_complex,
            0,
        ),
    ]


def _loops_allowed(func: CFunctionMetrics, exclusions: dict[str, Any]) -> bool:
    """函数名白名单或路径 glob（如 ``kernel/**``）命中则允许必要单层循环."""
    if func.name in set(exclusions.get("loop_allowed_functions", [])):
        return True
    patterns = list(exclusions.get("loop_allowed_file_patterns", []))
    return any(fnmatch.fnmatch(func.file_key, pattern) for pattern in patterns)


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """统一违规记录字段."""
    return {"target": target, "issue": issue, "current": str(current), "limit": str(limit)}
