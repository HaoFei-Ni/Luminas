"""C/CUDA 循环嵌套扫描：门禁「单函数嵌套深度 ≤1、默认禁止循环」的数据源.

为何手写扫描而非 libclang：
- 门禁需在无编译数据库的 pre-commit/CI 秒级跑通；
- 只关心 for/while/do 的嵌套深度与语句个数，不需要完整 AST。

关键不变量：
- 深度按「进入循环体」计（单层 for = 1；for 内 for = 2）；
- 先剥离 // 与粗粒度字符串，避免 ``for`` 出现在字面量里误报；
- ``peak``/``count`` 用单元素 list 做可变累加器，避免深层返回元组。
"""

from __future__ import annotations

import re

# 词边界：避免匹配 perform / underflow 等含 for/do 子串的标识符。
_LOOP_HEAD = re.compile(r"\b(for|while|do)\b")


def scan_loops(body_lines: list[str]) -> tuple[int, int]:
    """扫描函数体，返回 ``(最大嵌套深度, 循环语句个数)``.

    Args:
        body_lines: 含定义花括号的函数全文行（与 metrics 切出的 span 一致）。

    Returns:
        peak nesting（无循环为 0）与循环头出现次数。
    """
    # 拼成单字符串：跨行 ``for (...)\n{`` 才能被同一索引窗口吃到。
    text = "\n".join(_strip_line(line) for line in body_lines)
    peak = [0]
    count = [0]
    index = 0
    length = len(text)
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    while index < length:
        match = _LOOP_HEAD.match(text, index)
        if match:
            # base_active=0：顶层循环深度从 1 起算。
            index = _consume_loop(text, match, index, 0, peak, count)
        else:
            index += 1
    return peak[0], count[0]


def max_loop_nesting(body_lines: list[str]) -> int:
    """仅返回最大嵌套深度（1=仅单层；≥2 触犯 eng-standard）."""
    return scan_loops(body_lines)[0]


def _strip_line(line: str) -> str:
    """去掉行尾 // 注释，并把字符串/字符字面量压成空串.

    粗粒度即可：门禁目标是防假阳性，不是完美 C 词法分析。
    """
    if "//" in line:
        line = line[: line.index("//")]
    # 用 "" 占位保留长度量级，避免把 ``for`` 从 ``"for"`` 里抠掉后拼接错位。
    return re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", '""', line)


def _consume_loop(
    text: str,
    match: re.Match[str],
    index: int,
    base_active: int,
    peak: list[int],
    count: list[int],
) -> int:
    """消费一个循环头，更新 peak/count，返回体结束后的下标.

    ``base_active`` 是外层已进入的循环层数；本循环深度 = base_active+1。
    """
    active = base_active + 1
    peak[0] = max(peak[0], active)
    count[0] += 1
    kind = match.group(1)
    index = match.end()
    if kind == "do":
        # do 的条件在体后：必须先吃体再吃 while(...);
        return _consume_do_body(text, index, active, peak, count)
    # for/while：先跳过控制括号，再进体（否则把 for(;;) 里的分号当语句结束）。
    index = _skip_parens(text, index)
    return _consume_for_while_body(text, index, active, peak, count)


def _consume_for_while_body(text: str, start: int, active: int, peak: list[int], count: list[int]) -> int:
    """跳过 for/while 循环体；体可以是块、嵌套循环或单语句."""
    index = _skip_space(text, start)
    if index < len(text) and text[index] == "{":
        return _walk_block(text, index, active, peak, count)
    match = _LOOP_HEAD.match(text, index)
    if match:
        # 无花括号时内层循环仍算嵌套：``for (...) for (...) stmt;``
        return _consume_loop(text, match, index, active, peak, count)
    return _skip_stmt(text, index)


def _consume_do_body(text: str, start: int, active: int, peak: list[int], count: list[int]) -> int:
    """跳过 do 体，再可选消费尾部 ``while (...);``（不把尾 while 再计一次循环）."""
    index = _consume_for_while_body(text, start, active, peak, count)
    index = _skip_space(text, index)
    if text.startswith("while", index):
        # 这是 do-while 的条件，不是新的 while 语句。
        index = _skip_parens(text, index + 5)
        index = _skip_space(text, index)
        if index < len(text) and text[index] == ";":
            index += 1
    return index


def _walk_block(text: str, start: int, active: int, peak: list[int], count: list[int]) -> int:
    """在 ``{...}`` 内扫描嵌套循环；``depth`` 只跟踪本块花括号，与循环 active 正交."""
    index = start + 1
    depth = 1
    length = len(text)
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    while index < length and depth > 0:
        match = _LOOP_HEAD.match(text, index)
        if match:
            # 传入当前 active：块内再遇循环即嵌套 +1。
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
    """跳过非循环单语句直到分号；语句内若有 ``{}`` 整块跳过（如复合字面量）."""
    index = start
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    while index < len(text) and text[index] != ";":
        if text[index] == "{":
            index = _skip_braces(text, index)
            continue
        index += 1
    return index + 1 if index < len(text) else index


def _skip_parens(text: str, start: int) -> int:
    """跳过空白后的 ``(...)``；深度配对，避免 ``for (i; f(a,b); i++)`` 早停."""
    index = _skip_space(text, start)
    if index >= len(text) or text[index] != "(":
        return index
    depth = 0
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
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
    """跳过从 ``start`` 开始的完整 ``{...}`` 组."""
    depth = 0
    index = start
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
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
    """前进到下一个非空白字符."""
    index = start
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    while index < len(text) and text[index].isspace():
        index += 1
    return index
