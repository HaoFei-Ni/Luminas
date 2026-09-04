"""AST parsing helpers for inheritance-depth metrics."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def class_bases_map(
    file_key: str,
    path: Path,
    base_name: Callable[[ast.AST], str],
) -> dict[str, list[str]]:
    """Collect ``module.Class`` → base names from one source file."""
    mod = ".".join(Path(file_key).with_suffix("").parts)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: dict[str, list[str]] = {}
    # 单遍顶层：只收 ClassDef，避免嵌套类抬高假深度。
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        out[f"{mod}.{node.name}"] = [base_name(base) for base in node.bases]
    return out


def resolved_parent_depth(
    parent: str,
    child: str,
    bases: dict[str, list[str]],
    memo: dict[str, int],
    resolve_parent: Callable[[str, str, dict[str, list[str]]], str | None],
) -> int | None:
    """Resolved parent depth, 0 when unknown; None when parent depth not ready."""
    key = resolve_parent(parent, child, bases)
    if key is None:
        return 0
    if key not in memo:
        return None
    return memo[key]
