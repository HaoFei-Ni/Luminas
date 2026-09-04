"""Optional / None dereference risk counting for the HA gate."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from tools.checks.reliability.annot import optional_names
from tools.checks.reliability.guard import names_none_guarded

if TYPE_CHECKING:
    from pathlib import Path


def none_reference_risk(files: list[tuple[str, Path]]) -> tuple[int, str]:
    """Count Optional-annotated names used via attr/sub without a None guard."""
    total = 0
    locator = ""
    # 单遍：空引用是线上主因，未校验访问一律计风险。
    for file_key, path in files:
        count = _none_risk_in_tree(ast.parse(path.read_text(encoding="utf-8")))
        if count and not locator:
            locator = file_key
        total += count
    return total, locator


def _none_risk_in_tree(tree: ast.AST) -> int:
    """Sum Optional attr/subscript risks across functions and methods."""
    total = 0
    # 单遍顶层：类方法与自由函数同规则，避免漏检。
    for node in tree.body:
        total += _risk_from_toplevel(node)
    return total


def _risk_from_toplevel(node: ast.AST) -> int:
    """Score one module-level function or class for Optional risks."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _none_risk_in_function(node)
    if not isinstance(node, ast.ClassDef):
        return 0
    total = 0
    # 单遍方法：须复用函数规则，避免类内漏检。
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += _none_risk_in_function(item)
    return total


def _none_risk_in_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count unguarded attr/subscript uses of Optional-annotated locals/params."""
    optionals = optional_names(node)
    if not optionals:
        return 0
    risky = optionals - names_none_guarded(node)
    if not risky:
        return 0
    return _unguarded_loads(node, risky)


def _unguarded_loads(node: ast.AST, risky: set[str]) -> int:
    """Count Attribute/Subscript loads of names in ``risky``."""
    count = 0
    # 单遍：属性/下标即解引用，无防护则计一次风险。
    for stmt in ast.walk(node):
        if (
            isinstance(stmt, (ast.Attribute, ast.Subscript))
            and isinstance(stmt.value, ast.Name)
            and stmt.value.id in risky
        ):
            count += 1
    return count
