"""C/C++/CUDA documentation-comment detectors (eng-standard / LUM-ENG-101).

Policy (why, not what):
- Every translation unit starts with a file banner ``/* ... */`` or ``//``.
- Every function *definition* has a leading doc comment.
- Every exported prototype in a header has a leading doc comment.
"""

from __future__ import annotations

import re

_FUNC_PROTO = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*;"
)
_CONTROL = frozenset({"if", "for", "while", "switch", "do", "return"})


def has_file_banner(lines: list[str]) -> bool:
    """Return True when the file opens with a block or line documentation banner."""
    text = "\n".join(lines).lstrip("\ufeff").lstrip()
    return text.startswith("/*") or text.startswith("//")


def has_leading_doc_comment(lines: list[str], start_line: int) -> bool:
    """Return True when ``start_line`` (1-based) is preceded by a doc comment."""
    index = start_line - 2
    while index >= 0 and not lines[index].strip():
        index -= 1
    if index < 0:
        return False
    stripped = lines[index].strip()
    if stripped.startswith("//"):
        return True
    return stripped.endswith("*/")


def undocumented_prototypes(lines: list[str]) -> list[tuple[str, int]]:
    """Return ``(name, line)`` for header prototypes lacking a leading doc comment."""
    missing: list[tuple[str, int]] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if _skip_noise(stripped):
            index += 1
            continue
        name, end = _prototype_at(lines, index)
        if name is None or end is None:
            index += 1
            continue
        if not has_leading_doc_comment(lines, index + 1):
            missing.append((name, index + 1))
        index = end + 1
    return missing


def _skip_noise(stripped: str) -> bool:
    """Skip blanks, preprocessor, and comment-only lines (incl. ``*`` bodies)."""
    return (
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped == "*/"
        or stripped.startswith("*")
        or stripped.startswith("{")
        or stripped.startswith("}")
        or stripped in {'extern "C" {', 'extern "C"{'}
        or stripped.startswith("namespace")
        or stripped.startswith("using ")
        or stripped.startswith("typedef")
        or stripped.startswith("struct")
        or stripped.startswith("enum")
        or stripped.startswith("class")
    )


def _prototype_at(lines: list[str], start: int) -> tuple[str | None, int | None]:
    """Parse a ``name(...);`` prototype starting at ``start``; return name and end index."""
    window: list[str] = []
    for index in range(start, min(start + 12, len(lines))):
        window.append(lines[index].rstrip())
        joined = " ".join(part.strip() for part in window)
        if "{" in joined:
            return None, None
        if ";" not in joined:
            continue
        match = _FUNC_PROTO.search(joined)
        if match is None:
            return None, None
        name = match.group(1)
        if name in _CONTROL:
            return None, None
        return name, index
    return None, None
