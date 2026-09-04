"""Python AST helpers: detect self-recursive function definitions."""

from __future__ import annotations

import ast


def self_recursive_names(tree: ast.AST) -> set[str]:
    """Return names of functions that call themselves (direct recursion)."""
    recursive: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _calls_name(node, node.name):
            recursive.add(node.name)
    return recursive


def _calls_name(node: ast.AST, name: str) -> bool:
    """Return True when ``node`` contains a Call to bare name ``name``."""
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
    return False
