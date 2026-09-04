"""C 函数 span 切分：定义名 + 花括号配对.

从 ``c_quality_metrics`` 拆出，压低单文件函数数与 span 解析认知/嵌套复杂度。
"""

from __future__ import annotations

import re

_CONTROL = frozenset({"if", "for", "while", "switch", "do"})
_FUNC_DEF = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*\{"
)


def function_spans(lines: list[str]) -> list[tuple[str, int, int]]:
    """用花括号配对切出 ``(name, start_line, end_line)``（1-based，含端点）."""
    spans: list[tuple[str, int, int]] = []
    index = 0
    # 单遍：跳过注释/预处理后定位定义，避免嵌套静态函数重复计数。
    while index < len(lines):
        if _skip_line(lines[index].strip()):
            index += 1
            continue
        span = _try_span_at(lines, index)
        if span is None:
            index += 1
            continue
        spans.append(span)
        # 跳到函数结束后，避免嵌套静态函数被外层重复扫描（少见但安全）。
        index = span[2]
    return spans


def _try_span_at(lines: list[str], start: int) -> tuple[str, int, int] | None:
    """If ``start`` begins a definition, return ``(name, start_line, end_line)``."""
    name = _definition_name_at(lines, start)
    brace_line = _opening_brace_line(lines, start) if name else None
    end = match_braces(lines, brace_line) if brace_line is not None else None
    if name is None or brace_line is None or end is None:
        return None
    return name, start + 1, end + 1


def _skip_line(stripped: str) -> bool:
    """跳过空白、预处理、注释行."""
    if not stripped:
        return True
    prefixes = ("#", "//", "/*", "*")
    return stripped == "*/" or stripped.startswith(prefixes)


def _definition_name_at(lines: list[str], start: int) -> str | None:
    """若 ``start`` 起是函数定义（非原型），返回函数名."""
    window: list[str] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for index in range(start, min(start + 12, len(lines))):
        window.append(lines[index].rstrip())
        joined = " ".join(part.strip() for part in window)
        # 仅有分号、无花括号 → 原型，交给头文件文档检查。
        if ";" in joined and "{" not in joined:
            return None
        if "{" not in joined:
            continue
        return _name_from_joined(joined)
    return None


def _name_from_joined(joined: str) -> str | None:
    """Parse a function name from a joined definition window that contains ``{``."""
    match = _FUNC_DEF.search(joined)
    if match is None:
        return None
    name = match.group(1)
    return None if name in _CONTROL else name


def _opening_brace_line(lines: list[str], start: int) -> int | None:
    """定义起始行起找首个 ``{``；途中先遇 ``;`` 则不是定义."""
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for index in range(start, min(start + 12, len(lines))):
        if "{" in lines[index]:
            return index
        if ";" in lines[index]:
            return None
    return None


def match_braces(lines: list[str], start: int) -> int | None:
    """从 ``start`` 行的首个 ``{`` 配对到同深度 ``}``，返回结束行下标."""
    depth = 0
    started = False
    # 单遍：逐字符调深度，避免嵌套 for/if 抬高控制嵌套。
    for index in range(start, len(lines)):
        end = _brace_line_end(lines[index], depth, started)
        if end[0]:
            return index
        depth, started = end[1], end[2]
    return None


def _brace_line_end(line: str, depth: int, started: bool) -> tuple[bool, int, bool]:
    """Apply one source line to brace depth; return (done, depth, started)."""
    # 单遍：字符级配对，闭合即结束，避免嵌套深度漂移。
    for char in line:
        if char == "{":
            depth += 1
            started = True
            continue
        if char != "}":
            continue
        depth -= 1
        if started and depth == 0:
            return True, depth, started
    return False, depth, started
