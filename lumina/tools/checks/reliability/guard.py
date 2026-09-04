"""None-guard detection for Optional names."""

from __future__ import annotations

import ast


def names_none_guarded(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names that appear in ``is None`` / truthiness / ``assert name`` checks."""
    guarded: set[str] = set()
    # 单遍：显式 None 或真值判定即视为该名已防护。
    for stmt in ast.walk(node):
        guarded.update(_guard_names_from(stmt))
    return guarded


def _guard_names_from(stmt: ast.AST) -> set[str]:
    """Extract names protected by compare / assert / if truthiness guards."""
    if isinstance(stmt, ast.Assert) and isinstance(stmt.test, ast.Name):
        return {stmt.test.id}
    if isinstance(stmt, ast.Compare):
        return guard_from_compare(stmt)
    if isinstance(stmt, ast.If):
        return _guard_from_if_test(stmt.test)
    return set()


def _guard_from_if_test(test: ast.AST) -> set[str]:
    """Names guarded by ``if name`` / ``if not name`` / None compares."""
    if isinstance(test, ast.Name):
        return {test.id}
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and isinstance(test.operand, ast.Name):
        return {test.operand.id}
    if isinstance(test, ast.Compare):
        return guard_from_compare(test)
    return set()


def _name_none_pair(name_side: ast.AST, other_side: ast.AST) -> str | None:
    """Return guarded name when ``name_side`` is compared to ``None``."""
    if isinstance(name_side, ast.Name) and _is_none_constant(other_side):
        return name_side.id
    return None


def _is_none_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def guard_from_compare(node: ast.Compare) -> set[str]:
    """Names compared with ``None`` on either side of a Compare."""
    names: set[str] = set()
    comps = [node.left, *node.comparators]
    # 成对扫描：一侧 Name、一侧 None 即记防护。
    for left, right in zip(comps, comps[1:], strict=False):
        guarded = _name_none_pair(left, right) or _name_none_pair(right, left)
        if guarded is not None:
            names.add(guarded)
    return names
