"""Python AST：检测直接自递归函数定义.

供 Python 门禁复用；与 C 侧 ``c_recursion`` 语义对齐（只查直接自调用）。
"""

from __future__ import annotations

import ast


def self_recursive_names(tree: ast.AST) -> set[str]:
    """返回直接调用自身的函数名集合（含 async）."""
    recursive: set[str] = set()
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _calls_name(node, node.name):
            recursive.add(node.name)
    return recursive


def _calls_name(node: ast.AST, name: str) -> bool:
    """``node`` 子树是否含对裸名 ``name`` 的 Call.

    只认 ``Name``，不认 ``obj.name`` 属性调用，避免把方法转发误判成递归。
    """
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
    return False
