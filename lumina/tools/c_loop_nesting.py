"""Loop-nesting depth scanner for C/CUDA function bodies."""

from __future__ import annotations

import re

_LOOP_HEAD = re.compile(r"\b(for|while|do)\b")


def scan_loops(body_lines: list[str]) -> tuple[int, int]:
    """Return ``(max_nesting_depth, loop_statement_count)`` for a function body."""
    text = "\n".join(_strip_line(line) for line in body_lines)
    peak = [0]
    count = [0]
    index = 0
    length = len(text)
    while index < length:
        match = _LOOP_HEAD.match(text, index)
        if match:
            index = _consume_loop(text, match, index, 0, peak, count)
        else:
            index += 1
    return peak[0], count[0]


def max_loop_nesting(body_lines: list[str]) -> int:
    """Return max nested loop depth (1 = single-level only; ≥2 is forbidden)."""
    return scan_loops(body_lines)[0]


def _strip_line(line: str) -> str:
    """Drop // comments and rough string/char literals."""
    if "//" in line:
        line = line[: line.index("//")]
    return re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", '""', line)


def _consume_loop(
    text: str,
    match: re.Match[str],
    index: int,
    base_active: int,
    peak: list[int],
    count: list[int],
) -> int:
    """Parse one loop at base_active+1 and return the index after its body."""
    active = base_active + 1
    peak[0] = max(peak[0], active)
    count[0] += 1
    kind = match.group(1)
    index = match.end()
    if kind == "do":
        return _consume_do_body(text, index, active, peak, count)
    index = _skip_parens(text, index)
    return _consume_for_while_body(text, index, active, peak, count)


def _consume_for_while_body(text: str, start: int, active: int, peak: list[int], count: list[int]) -> int:
    """Skip the body of a for/while at the given active nesting depth."""
    index = _skip_space(text, start)
    if index < len(text) and text[index] == "{":
        return _walk_block(text, index, active, peak, count)
    match = _LOOP_HEAD.match(text, index)
    if match:
        return _consume_loop(text, match, index, active, peak, count)
    return _skip_stmt(text, index)


def _consume_do_body(text: str, start: int, active: int, peak: list[int], count: list[int]) -> int:
    """Skip do-body then optional ``while (...);`` tail."""
    index = _consume_for_while_body(text, start, active, peak, count)
    index = _skip_space(text, index)
    if text.startswith("while", index):
        index = _skip_parens(text, index + 5)
        index = _skip_space(text, index)
        if index < len(text) and text[index] == ";":
            index += 1
    return index


def _walk_block(text: str, start: int, active: int, peak: list[int], count: list[int]) -> int:
    """Walk a ``{...}`` block, consuming nested loops at this active depth."""
    index = start + 1
    depth = 1
    length = len(text)
    while index < length and depth > 0:
        match = _LOOP_HEAD.match(text, index)
        if match:
            index = _consume_loop(text, match, index, active, peak, count)
            continue
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        index += 1
    return index


def _skip_stmt(text: str, start: int) -> int:
    """Skip a non-loop statement through its terminating semicolon."""
    index = start
    while index < len(text) and text[index] != ";":
        if text[index] == "{":
            index = _skip_braces(text, index)
            continue
        index += 1
    return index + 1 if index < len(text) else index


def _skip_parens(text: str, start: int) -> int:
    """Skip whitespace then a ``(...)`` group."""
    index = _skip_space(text, start)
    if index >= len(text) or text[index] != "(":
        return index
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return index


def _skip_braces(text: str, start: int) -> int:
    """Skip a ``{...}`` group that begins at start."""
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return index


def _skip_space(text: str, start: int) -> int:
    """Advance past whitespace."""
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    return index
