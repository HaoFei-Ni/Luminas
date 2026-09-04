"""C/CUDA structural metrics for eng-standard size / loop / recursion / docs.

Measures physical lines, per-function spans, loop nesting/count, self-recursion,
and whether each function has a leading documentation comment.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from tools.c_doc_comments import has_file_banner, has_leading_doc_comment
from tools.c_loop_nesting import scan_loops
from tools.c_recursion import has_self_recursion

_C_SUFFIXES = {".c", ".h", ".cu", ".cuh", ".cpp", ".hpp", ".cc"}
_CONTROL = frozenset({"if", "for", "while", "switch", "do"})
_FUNC_DEF = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*\{"
)


@dataclass(frozen=True)
class CFunctionMetrics:
    """One C/CUDA/C++ function: size, loops, recursion, and doc-comment flag."""

    file_key: str
    name: str
    lines: int
    start_line: int
    loop_nesting: int
    loop_count: int
    has_recursion: bool
    has_doc_comment: bool


@dataclass(frozen=True)
class CFileMetrics:
    """Per-file physical lines, function count, and file-banner flag."""

    file_key: str
    path: str
    lines: int
    function_count: int
    is_header: bool
    has_file_banner: bool


def as_file_key(path: str | Path) -> str:
    """Normalize a path to a forward-slash key."""
    return Path(path).as_posix()


def collect_c_files(roots: list[str], exclude_patterns: list[str]) -> list[Path]:
    """Collect sorted C/CUDA sources under roots, applying fnmatch excludes."""
    found: list[Path] = []
    for root in roots:
        found.extend(_collect_root(Path(root)))
    return sorted(
        {path for path in found if not any(fnmatch.fnmatch(as_file_key(path), pattern) for pattern in exclude_patterns)}
    )


def measure_c_files(
    paths: list[str],
    exclude_patterns: list[str],
) -> tuple[list[CFileMetrics], list[CFunctionMetrics]]:
    """Measure file size and per-function size / loops / recursion."""
    files: list[CFileMetrics] = []
    functions: list[CFunctionMetrics] = []
    for path in collect_c_files(paths, exclude_patterns):
        file_metrics, func_metrics = _measure_one(path)
        files.append(file_metrics)
        functions.extend(func_metrics)
    return files, functions


def _collect_root(base: Path) -> list[Path]:
    """Collect C/CUDA paths from one file or directory root."""
    if base.is_file() and base.suffix in _C_SUFFIXES:
        return [base]
    if not base.is_dir():
        return []
    return [path for path in base.rglob("*") if path.is_file() and path.suffix in _C_SUFFIXES]


def _measure_one(path: Path) -> tuple[CFileMetrics, list[CFunctionMetrics]]:
    """Measure one source file into file + function metrics."""
    raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    file_key = as_file_key(path)
    spans = _function_spans(raw_lines)
    file_metrics = CFileMetrics(
        file_key=file_key,
        path=str(path),
        lines=_count_physical(raw_lines),
        function_count=len(spans),
        is_header=path.suffix in {".h", ".cuh", ".hpp"},
        has_file_banner=has_file_banner(raw_lines),
    )
    functions: list[CFunctionMetrics] = []
    for name, start, end in spans:
        body = raw_lines[start - 1 : end]
        nesting, count = scan_loops(body)
        functions.append(
            CFunctionMetrics(
                file_key=file_key,
                name=name,
                lines=_count_physical(body),
                start_line=start,
                loop_nesting=nesting,
                loop_count=count,
                has_recursion=has_self_recursion(name, body),
                has_doc_comment=has_leading_doc_comment(raw_lines, start),
            )
        )
    return file_metrics, functions


def _count_physical(lines: list[str]) -> int:
    """Count non-blank, non-full-line-comment physical lines."""
    return sum(1 for line in lines if _is_physical(line.strip()))


def _is_physical(stripped: str) -> bool:
    """Return True when a stripped line counts toward size gates."""
    return (
        bool(stripped) and not stripped.startswith("//") and not (stripped.startswith("/*") and stripped.endswith("*/"))
    )


def _function_spans(lines: list[str]) -> list[tuple[str, int, int]]:
    """Extract (name, start_line, end_line) via brace matching on definitions."""
    spans: list[tuple[str, int, int]] = []
    index = 0
    while index < len(lines):
        if _skip_line(lines[index].strip()):
            index += 1
            continue
        name = _definition_name_at(lines, index)
        brace_line = _opening_brace_line(lines, index) if name else None
        end = _match_braces(lines, brace_line) if brace_line is not None else None
        if name is None or brace_line is None or end is None:
            index += 1
            continue
        spans.append((name, index + 1, end + 1))
        index = end + 1
    return spans


def _skip_line(stripped: str) -> bool:
    """Return True for blank, preprocessor, or comment-only lines.

    Block-comment bodies often start with ``*`` (Doxygen/file banners). Those
    must be skipped: otherwise prose like ``O(n)`` is mistaken for a function
    when a later ``{`` appears in the same parse window.
    """
    return (
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped == "*/"
        or stripped.startswith("*")
    )


def _definition_name_at(lines: list[str], start: int) -> str | None:
    """Return function name if ``start`` begins a definition (not a prototype)."""
    window: list[str] = []
    for index in range(start, min(start + 12, len(lines))):
        window.append(lines[index].rstrip())
        joined = " ".join(part.strip() for part in window)
        if ";" in joined and "{" not in joined:
            return None
        if "{" not in joined:
            continue
        match = _FUNC_DEF.search(joined)
        if match is None:
            return None
        name = match.group(1)
        return None if name in _CONTROL else name
    return None


def _opening_brace_line(lines: list[str], start: int) -> int | None:
    """Find the line containing the opening '{' of a definition starting at start."""
    for index in range(start, min(start + 12, len(lines))):
        if "{" in lines[index]:
            return index
        if ";" in lines[index]:
            return None
    return None


def _match_braces(lines: list[str], start: int) -> int | None:
    """Return the line index of the closing brace matching the first '{'."""
    depth = 0
    started = False
    for index in range(start, len(lines)):
        for char in lines[index]:
            if char == "{":
                depth += 1
                started = True
            elif char == "}":
                depth -= 1
                if started and depth == 0:
                    return index
    return None
