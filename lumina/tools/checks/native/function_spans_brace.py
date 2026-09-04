"""Brace-depth helpers for ``function_spans`` (split to stay under per-file function cap)."""

from __future__ import annotations


def brace_line_end(line: str, depth: int, started: bool) -> tuple[bool, int, bool]:
    """Apply one source line to brace depth; return (done, depth, started)."""
    # 必须逐字符配对：闭合到深度 0 即函数结束。
    for char in line:
        done, depth, started = _apply_brace_char(char, depth, started)
        if done:
            return True, depth, started
    return False, depth, started


def _apply_brace_char(char: str, depth: int, started: bool) -> tuple[bool, int, bool]:
    """Update brace depth for one character; signal when outermost block closes."""
    if char == "{":
        return False, depth + 1, True
    if char != "}":
        return False, depth, started
    depth -= 1
    if started and depth == 0:
        return True, depth, started
    return False, depth, started
