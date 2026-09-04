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


def guard_from_compare(node: ast.Compare) -> set[str]:
    """Names compared with ``None`` on either side of a Compare."""
    names: set[str] = set()
    comps = [node.left, *node.comparators]
    # 成对扫描：一侧 Name、一侧 None 即记防护。
    for left, right in zip(comps, comps[1:], strict=False):
        if isinstance(left, ast.Name) and isinstance(right, ast.Constant) and right.value is None:
            names.add(left.id)
        if isinstance(right, ast.Name) and isinstance(left, ast.Constant) and left.value is None:
            names.add(right.id)
    return names
