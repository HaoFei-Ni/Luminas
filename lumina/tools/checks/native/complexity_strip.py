"""Comment/string stripping for C complexity measurement."""

from __future__ import annotations


def strip_comments_and_strings(source: str) -> str:
    """Remove // and /* */ comments and quoted strings to avoid false keywords."""
    out: list[str] = []
    i = 0
    n = len(source)
    # 必须状态机剥离：注释/字符串内的 if 不得计入复杂度。
    while i < n:
        i, chunk = _strip_step(source, i)
        if chunk is not None:
            out.append(chunk)
    return "".join(out)


def _strip_step(source: str, index: int) -> tuple[int, str | None]:
    """Advance strip scan one token; return (next_index, literal to append or None)."""
    if source.startswith("//", index):
        return skip_line(source, index), "\n"
    if source.startswith("/*", index):
        return skip_block_comment(source, index), None
    if source[index] in {'"', "'"}:
        return skip_string(source, index, source[index]), '""'
    return index + 1, source[index]


def skip_line(source: str, index: int) -> int:
    """Skip from ``//`` to end of line."""
    end = source.find("\n", index)
    return len(source) if end < 0 else end + 1


def skip_block_comment(source: str, index: int) -> int:
    """Skip from ``/*`` through closing ``*/``."""
    end = source.find("*/", index + 2)
    return len(source) if end < 0 else end + 2


def skip_string(source: str, index: int, quote: str) -> int:
    """Skip a quoted string literal starting at ``index``."""
    i = index + 1
    n = len(source)
    # 必须处理转义：避免 \" 提前结束字符串扫描。
    while i < n:
        if source[i] == quote:
            return i + 1
        i = _string_next_index(source, i, n)
    return n


def _string_next_index(source: str, index: int, length: int) -> int:
    """Advance one character inside a string, skipping backslash escapes."""
    if source[index] == "\\" and index + 1 < length:
        return index + 2
    return index + 1
