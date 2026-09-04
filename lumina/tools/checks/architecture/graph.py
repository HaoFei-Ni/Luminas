"""First-party import graph construction (fan-out edges)."""

from __future__ import annotations

import ast
from pathlib import Path

_FIRST_PARTY = frozenset({"tools", "tests", "theory"})


def module_name(file_key: str) -> str:
    """Map ``tools/foo.py`` → ``tools.foo``; ``__init__.py`` → package name."""
    path = Path(file_key)
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_import_graph(files: list[tuple[str, Path]]) -> dict[str, set[str]]:
    """Return module → set of first-party modules it imports."""
    known = {module_name(key) for key, _ in files}
    graph: dict[str, set[str]] = {name: set() for name in known}
    # 单遍建图：须只计一方导入边，避免把第三方依赖算进扇出。
    for file_key, path in files:
        src = module_name(file_key)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        graph[src].update(_imports_from_tree(tree, src, known))
    return graph


def _imports_from_tree(tree: ast.AST, src: str, known: set[str]) -> set[str]:
    """Collect first-party modules referenced by Import / ImportFrom."""
    found: set[str] = set()
    # 单遍 walk：边界由 AST 保证，避免重复解析抬高嵌套。
    for node in ast.walk(tree):
        found.update(_imports_of_node(node, src, known))
    found.discard(src)
    return found


def _imports_of_node(node: ast.AST, src: str, known: set[str]) -> set[str]:
    """Resolve one AST node into zero or more first-party module names."""
    if isinstance(node, ast.Import):
        return _imports_of_import(node, known)
    if isinstance(node, ast.ImportFrom):
        target = _resolve_from(node, src, known)
        return {target} if target else set()
    return set()


def _imports_of_import(node: ast.Import, known: set[str]) -> set[str]:
    """Map each ``import a.b`` alias to the longest known first-party prefix."""
    out: set[str] = set()
    # 单遍 alias：须独立匹配，避免漏计多名称 import。
    for alias in node.names:
        match = _longest_known(alias.name, known)
        if match:
            out.add(match)
    return out


def _resolve_from(node: ast.ImportFrom, src: str, known: set[str]) -> str | None:
    """Resolve ``from .x import`` / ``from tools.x import`` to a known module."""
    if node.level and node.level > 0:
        return _relative_module(src, node.level, node.module, known)
    if not node.module:
        return None
    return _longest_known(node.module, known)


def _relative_module(src: str, level: int, module: str | None, known: set[str]) -> str | None:
    """Resolve relative import against ``src`` package path."""
    parts = src.split(".")
    if len(parts) < level:
        return None
    base = parts[: len(parts) - level]
    if module is not None:
        base.extend(module.split("."))
    return _longest_known(".".join(base), known)


def _longest_known(name: str, known: set[str]) -> str | None:
    """Prefer the longest known module prefix of ``name``."""
    parts = name.split(".")
    # 从长到短：tools.a.b 优先于 tools.a，避免扇出低估。
    for end in range(len(parts), 0, -1):
        candidate = ".".join(parts[:end])
        if candidate in known and candidate.split(".", 1)[0] in _FIRST_PARTY:
            return candidate
    return None
