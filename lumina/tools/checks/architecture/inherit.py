"""Inheritance-depth metrics for the architecture gate."""

from __future__ import annotations

import ast
from pathlib import Path


def max_inheritance_depth(files: list[tuple[str, Path]]) -> tuple[int, str]:
    """Return (max inheritance depth, class locator) among project classes."""
    bases = _collect_bases(files)
    depths = _compute_depths(bases)
    if not depths:
        return 0, ""
    best_name = max(depths, key=depths.get)
    return depths[best_name], best_name


def _collect_bases(files: list[tuple[str, Path]]) -> dict[str, list[str]]:
    """Map ``module.Class`` → list of simple base names (unresolved ok)."""
    bases: dict[str, list[str]] = {}
    # 单遍文件：须合并各类表，避免漏扫多文件继承链。
    for file_key, path in files:
        bases.update(_bases_in_file(file_key, path))
    return bases


def _bases_in_file(file_key: str, path: Path) -> dict[str, list[str]]:
    """Collect ClassDef base names from one source file."""
    mod = ".".join(Path(file_key).with_suffix("").parts)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: dict[str, list[str]] = {}
    # 单遍顶层：只收 ClassDef，避免嵌套类抬高假深度。
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            # 单遍 bases：须扁平化 Name/Attribute，避免动态基类炸解析。
            out[f"{mod}.{node.name}"] = [_base_name(base) for base in node.bases]
    return out


def _base_name(node: ast.AST) -> str:
    """Extract a simple name from a base expression when possible."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _resolve_parent(parent: str, child: str, bases: dict[str, list[str]]) -> str | None:
    """Resolve ``Parent`` to same-module or unique global match."""
    if not parent:
        return None
    mod = child.rsplit(".", 1)[0]
    same = f"{mod}.{parent}"
    if same in bases:
        return same
    # 单遍全局：仅唯一短名可绑，避免同名类歧义错链。
    matches = [key for key in bases if key.endswith(f".{parent}")]
    if len(matches) == 1:
        return matches[0]
    return None


def _compute_depths(bases: dict[str, list[str]]) -> dict[str, int]:
    """Iteratively assign depth 1 for roots; else 1 + max parent depth."""
    memo: dict[str, int] = {}
    # 有界轮转：须破环，避免相互继承死循环。
    for _ in range(len(bases) + 1):
        if not _depth_pass(bases, memo):
            break
    # 残留环节点置 1：必须可终止，防止门禁挂死。
    for name in bases:
        memo.setdefault(name, 1)
    return memo


def _depth_pass(bases: dict[str, list[str]], memo: dict[str, int]) -> bool:
    """One saturation pass; True when at least one class depth was newly set."""
    progressed = False
    # 单遍类表：父类未就绪则跳过，避免用半成品深度污染。
    for name, parents in bases.items():
        if name in memo:
            continue
        depth = _ready_depth(name, parents, bases, memo)
        if depth is None:
            continue
        memo[name] = depth
        progressed = True
    return progressed


def _ready_depth(
    name: str,
    parents: list[str],
    bases: dict[str, list[str]],
    memo: dict[str, int],
) -> int | None:
    """Return depth when all parents resolve; else None."""
    if not parents or parents == [""]:
        return 1
    resolved: list[int] = []
    # 单遍父类：任一未入 memo 则整类推迟，避免环上读脏。
    for parent in parents:
        key = _resolve_parent(parent, name, bases)
        if key is None:
            resolved.append(0)
            continue
        if key not in memo:
            return None
        resolved.append(memo[key])
    return 1 + max(resolved, default=0)
