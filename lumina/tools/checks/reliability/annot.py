"""Annotation helpers for Optional / ``X | None`` detection."""

from __future__ import annotations

import ast


def optional_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names annotated as Optional / ``X | None`` in args or AnnAssign."""
    names: set[str] = set()
    # 单遍参数：注解即契约，须在使用前校验。
    for arg in [*node.args.args, *node.args.kwonlyargs, *node.args.posonlyargs]:
        if arg.annotation is not None and annotation_optional(arg.annotation):
            names.add(arg.arg)
    names.update(_ann_assign_optionals(node))
    return names


def annotation_optional(node: ast.AST) -> bool:
    """True when annotation is Optional[...] or a union containing None."""
    stack = [node]
    # 显式栈：须破嵌套 BinOp，避免自递归触发门禁。
    while stack:
        if _node_is_optional(stack.pop(), stack):
            return True
    return False


def _optional_ann_name(stmt: ast.AST) -> str | None:
    """Return AnnAssign target name when annotation is Optional-like."""
    if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
        return None
    if stmt.annotation is None or not annotation_optional(stmt.annotation):
        return None
    return stmt.target.id


def _ann_assign_optionals(node: ast.AST) -> set[str]:
    """Collect AnnAssign targets whose annotation is Optional-like."""
    names: set[str] = set()
    # 单遍体：局部 Optional 同样须防护后再解引用。
    for stmt in ast.walk(node):
        name = _optional_ann_name(stmt)
        if name is not None:
            names.add(name)
    return names


def _is_optional_subscript(node: ast.AST) -> bool:
    return isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "Optional"


def _node_is_optional(cur: ast.AST, stack: list[ast.AST]) -> bool:
    """Push children onto stack; return True when ``cur`` itself denotes None/Optional."""
    if isinstance(cur, ast.Constant) and cur.value is None:
        return True
    if _is_optional_subscript(cur):
        return True
    if isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.BitOr):
        stack.extend((cur.left, cur.right))
    return False
