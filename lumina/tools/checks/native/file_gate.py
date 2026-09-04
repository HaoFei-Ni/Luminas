"""C 文件级结构/文档违规检查.

从 ``tools.checks.native.gate`` 拆出，避免单文件函数数与文件级检查认知复杂度超限。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from tools.checks.native.doc_comments import undocumented_prototypes

if TYPE_CHECKING:
    from tools.checks.native.metrics import CFileMetrics


def file_structure_violations(files: list[CFileMetrics], config: dict[str, Any]) -> list[dict[str, str]]:
    """校验单文件物理行数与函数个数上限."""
    thresholds = config["c_thresholds"]
    features = config["c_features"]
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for item in files:
        violations.extend(_one_file_size(item, features, thresholds))
    return violations


def doc_file_violations(files: list[CFileMetrics], features: dict[str, Any]) -> list[dict[str, str]]:
    """校验文件 banner 与头文件原型文档（开关来自 comment_standard）."""
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for item in files:
        violations.extend(_one_file_docs(item, features))
    return violations


def _one_file_size(
    item: CFileMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
) -> list[dict[str, str]]:
    """Emit size/count violations for one C file."""
    out: list[dict[str, str]] = []
    limit = thresholds["max_header_physical_lines"] if item.is_header else thresholds["max_impl_physical_lines"]
    if features["enable_file_lines_check"] and item.lines > limit:
        kind = "头文件" if item.is_header else "实现文件"
        out.append(_violation(item.file_key, f"C{kind}物理行数超限", item.lines, limit))
    max_funcs = thresholds["max_functions_per_file"]
    if features["enable_function_count_check"] and item.function_count > max_funcs:
        out.append(_violation(item.file_key, "C单文件函数数量超限", item.function_count, max_funcs))
    return out


def _one_file_docs(item: CFileMetrics, features: dict[str, Any]) -> list[dict[str, str]]:
    """Emit banner/prototype-doc violations for one C file."""
    out: list[dict[str, str]] = []
    if features.get("enable_file_banner_check", True) and not item.has_file_banner:
        out.append(_violation(item.file_key, "C文件缺少文件头文档注释", 0, 1))
    if not (item.is_header and features.get("enable_header_decl_doc_check", True)):
        return out
    lines = Path(item.path).read_text(encoding="utf-8", errors="replace").splitlines()
    # 单遍：避免同一原型重复计数越界。
    for name, line in undocumented_prototypes(lines):
        out.append(_violation(f"{item.file_key}::{name}@{line}", "C头文件声明缺少前置文档注释", 0, 1))
    return out


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """统一违规记录字段."""
    return {"target": target, "issue": issue, "current": str(current), "limit": str(limit)}
