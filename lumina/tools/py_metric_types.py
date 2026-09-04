"""Shared Python metric types and path helpers (leaf module; no tools imports)."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionMetrics:
    """Per-function metrics: AST lines, complexities, nesting, self-recursion."""

    file_key: str
    name: str
    lines: int
    complexity: int | None
    has_recursion: bool = False
    cyclomatic: int | None = None
    control_nesting: int | None = None


@dataclass(frozen=True)
class FileMetrics:
    """Per-file metrics measured from AST (complexipy 8 no longer reports them)."""

    file_key: str
    path: str
    lines: int
    function_count: int


def as_file_key(path: str | Path) -> str:
    """Normalize a path to a forward-slash key relative to lumina/ when possible."""
    text = str(path).replace("\\", "/")
    if text.startswith("//?/"):
        text = text[4:]
    parts = Path(text).parts
    # 截到 lumina/ 之后：complexipy 绝对路径须与 scan 相对键对齐，避免认知复杂度漏检。
    for index, part in enumerate(parts):
        if part.lower() == "lumina" and index + 1 < len(parts):
            return Path(*parts[index + 1 :]).as_posix()
    return Path(text).as_posix()


def excluded(file_key: str, patterns: list[str]) -> bool:
    """Return True when a forward-slash key matches any fnmatch pattern."""
    return any(fnmatch.fnmatch(file_key, pattern) for pattern in patterns)
