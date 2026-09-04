"""Balanced paren/brace skip helpers for C loop nesting scans."""

from __future__ import annotations


def skip_space(text: str, start: int) -> int:
    """前进到下一个非空白字符."""
    index = start
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def skip_parens(text: str, start: int) -> int:
    """跳过空白后的 ``(...)``；深度配对，避免 ``for (i; f(a,b); i++)`` 早停."""
    index = skip_space(text, start)
    if index >= len(text) or text[index] != "(":
        return index
    return skip_balanced(text, index, "(", ")")


def advance_block_depth(char: str, depth: int) -> int:
    """Adjust brace depth for one character inside a block walk."""
    if char == "{":
        return depth + 1
    if char == "}":
        return depth - 1
    return depth


def skip_braces(text: str, start: int) -> int:
    """跳过从 ``start`` 开始的完整 ``{...}`` 组."""
    return skip_balanced(text, start, "{", "}")


def _balanced_step(char: str, depth: int, open_ch: str, close_ch: str) -> tuple[int, bool]:
    """Return updated depth and whether the balanced span closed."""
    if char == open_ch:
        return depth + 1, False
    if char != close_ch:
        return depth, False
    new_depth = depth - 1
    return new_depth, new_depth == 0


def skip_balanced(text: str, start: int, open_ch: str, close_ch: str) -> int:
    """Skip a balanced open/close pair starting at ``start`` (must be open_ch)."""
    depth = 0
    index = start
    # 单遍：深度归零即返回，避免嵌套 if 抬高控制嵌套。
    while index < len(text):
        char = text[index]
        index += 1
        depth, done = _balanced_step(char, depth, open_ch, close_ch)
        if done:
            return index
    return index
