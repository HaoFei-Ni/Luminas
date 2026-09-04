"""C source path and physical-line helpers for native metrics."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — used at runtime by is_c_source/collect_under_root

_C_SUFFIXES = frozenset({".c", ".h", ".cu", ".cuh", ".cpp", ".hpp", ".cc"})


def is_c_source(path: Path) -> bool:
    """True when ``path`` is a C/CUDA source or header file."""
    return path.is_file() and path.suffix in _C_SUFFIXES


def collect_under_root(base: Path) -> list[Path]:
    """Collect C/CUDA files under ``base`` (file or directory)."""
    if is_c_source(base):
        return [base]
    if not base.is_dir():
        return []
    return [path for path in base.rglob("*") if is_c_source(path)]


def is_physical_line(stripped: str) -> bool:
    """True when a stripped line counts toward physical line limits."""
    if not stripped or stripped.startswith("//"):
        return False
    return not (stripped.startswith("/*") and stripped.endswith("*/"))


def count_physical(lines: list[str]) -> int:
    """Count physical lines (exclude blank and whole-line comments)."""
    total = 0
    # 单遍：空行与整行注释不计物理行，避免虚高门禁行数。
    for line in lines:
        if is_physical_line(line.strip()):
            total += 1
    return total
