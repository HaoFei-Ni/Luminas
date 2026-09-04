"""Silent-exception path counting for the HA gate."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def unchecked_exception_paths(files: list[tuple[str, Path]]) -> tuple[int, str]:
    """Count silent ``except`` handlers (bare / pass-only); return (count, locator)."""
    total = 0
    locator = ""
    # 单遍文件：静默吞错会掩盖根因，必须计为未检异常路径。
    for file_key, path in files:
        count = _unchecked_in_tree(ast.parse(path.read_text(encoding="utf-8")))
        if count and not locator:
            locator = file_key
        total += count
    return total, locator


def _unchecked_in_tree(tree: ast.AST) -> int:
    """Count bare except and handlers whose body is only pass/ellipsis."""
    count = 0
    # 单遍 walk：须覆盖嵌套 try，避免漏检内层吞错。
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and _is_silent_handler(node):
            count += 1
    return count


def _is_silent_handler(node: ast.ExceptHandler) -> bool:
    """True for bare except or body that only pass / Ellipsis."""
    if node.type is None:
        return True
    body = [stmt for stmt in node.body if not _is_string_expr(stmt)]
    if not body:
        return True
    if len(body) != 1:
        return False
    return _is_pass_or_ellipsis(body[0])


def _is_string_expr(stmt: ast.stmt) -> bool:
    """True when statement is a string-literal docstring Expr."""
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)


def _is_pass_or_ellipsis(stmt: ast.stmt) -> bool:
    """True for ``pass`` or ``...`` expression statements."""
    if isinstance(stmt, ast.Pass):
        return True
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...
