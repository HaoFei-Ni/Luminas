"""Mutable module-global counting for the HA gate."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def max_global_state(files: list[tuple[str, Path]]) -> tuple[int, str]:
    """Return (max mutable module globals in one file, file_key)."""
    best = 0
    locator = ""
    # 单遍：取最坏文件，与 max_module_fan_out 同口径，避免漏报高状态模块。
    for file_key, path in files:
        count = _mutable_globals(ast.parse(path.read_text(encoding="utf-8")))
        if count > best:
            best = count
            locator = file_key
    return best, locator


def _mutable_globals(tree: ast.Module) -> int:
    """Count module-level bindings initialized to list/dict/set or their ctors."""
    count = 0
    # 单遍顶层：frozenset/常量不计，避免把只读配置误杀成状态。
    for node in tree.body:
        if isinstance(node, ast.Assign):
            count += _assign_mutable_names(node)
        elif (
            isinstance(node, ast.AnnAssign)
            and node.value is not None
            and isinstance(node.target, ast.Name)
            and node.target.id != "__all__"
            and _is_mutable(node.value)
        ):
            count += 1
    return count


def _assign_mutable_names(node: ast.Assign) -> int:
    """Count Name targets of a mutable Assign (skip ``__all__``)."""
    if not _is_mutable(node.value):
        return 0
    return sum(1 for t in node.targets if isinstance(t, ast.Name) and t.id != "__all__")


def _is_mutable(node: ast.AST) -> bool:
    """True for list/dict/set literals or dict/list/set/defaultdict calls."""
    if isinstance(node, (ast.List, ast.Dict, ast.Set)):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in {"dict", "list", "set", "defaultdict"}
    return False
