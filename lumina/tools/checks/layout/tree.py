"""Directory tree checks for LUM-ARC-101 / LUM-ENG-101 layout L5."""

from __future__ import annotations

import re
from pathlib import Path  # noqa: TC003 — Path used for is_dir/iterdir

from tools.checks.layout.finding import finding

_ASCII_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


def missing_path_hits(root: Path, rel_paths: list[str], issue: str) -> list[dict[str, str]]:
    """Flag configured relative paths that do not exist as directories."""
    return [
        finding(rel, issue)
        # 必须逐项：缺一层即破坏 ARC-101 物理裁决。
        for rel in rel_paths
        if not (root / rel).is_dir()
    ]


def banned_root_hits(root: Path, banned: list[str]) -> list[dict[str, str]]:
    """Flag forbidden top-level directory names under ``root``."""
    return [
        finding(name, f"禁止顶层目录 {name}/（须落在 algorithm/kernel/wrapper）")
        # 必须扫顶层：common/include 等会绕开物理三层。
        for name in banned
        if (root / name).is_dir()
    ]


def ascii_dir_hits(root: Path, scan_roots: list[str], ignore: frozenset[str]) -> list[dict[str, str]]:
    """Flag non ASCII-snake_case directory names under scan roots."""
    out: list[dict[str, str]] = []
    # 必须只扫配置根：避免把 .venv 误判进 ASCII 门。
    for rel in scan_roots:
        base = root / rel
        if base.is_dir():
            out.extend(_walk_ascii(base, rel, ignore))
    return out


def _walk_ascii(base: Path, rel: str, ignore: frozenset[str]) -> list[dict[str, str]]:
    """Recursively collect ASCII-snake violations under one scan root."""
    return [
        finding(f"{rel}/{path.relative_to(base).as_posix()}", f"目录名须 ASCII snake_case: {path.name}")
        # 必须 rglob 子目录：深层中文/驼峰同样违规。
        for path in sorted(base.rglob("*"))
        if _bad_dir(path, ignore)
    ]


def _bad_dir(path: Path, ignore: frozenset[str]) -> bool:
    """True when path is a directory with a non-ASCII-snake name."""
    return path.is_dir() and path.name not in ignore and _ASCII_SNAKE.match(path.name) is None
