"""复杂语句行扫描：邻接注释存在性 / why 语义.

从 ``inline_comments`` 拆出，压低主模块函数数与扫描认知复杂度。
"""

from __future__ import annotations

import re

from tools.inline_why import is_why_comment


def scan_uncommented(
    body_lines: list[str],
    pattern: re.Pattern[str],
    *,
    c_style: bool,
    require_why: bool,
) -> list[int]:
    """扫描 body，收集匹配 pattern 且邻接注释不足（或 why 不合格）的行号."""
    missing: list[int] = []
    # 单遍：复杂行集合有限，按行扫描即可避免重复读。
    for index, raw in enumerate(body_lines):
        if _line_needs_comment(body_lines, index, raw, pattern, c_style, require_why):
            missing.append(index + 1)
    return missing


def _line_needs_comment(
    body_lines: list[str],
    index: int,
    raw: str,
    pattern: re.Pattern[str],
    c_style: bool,
    require_why: bool,
) -> bool:
    """True when this line is complex and lacks a qualifying adjacent comment."""
    stripped = raw.strip()
    if not stripped or stripped in {"{", "}", "};"}:
        return False
    if _is_comment_only(stripped, c_style) or (c_style and stripped.startswith("#")):
        return False
    code = _strip_strings(_code_part(raw, c_style))
    if not pattern.search(code):
        return False
    return not _comment_ok(body_lines, index, c_style, require_why)


def _comment_ok(lines: list[str], index: int, c_style: bool, require_why: bool) -> bool:
    """True when adjacent comment exists and (if required) passes why heuristic."""
    note = _adjacent_comment_text(lines, index, c_style)
    if note is None:
        return False
    return (not require_why) or is_why_comment(note)


def _code_part(line: str, c_style: bool) -> str:
    """去掉行尾注释后的代码部分，避免注释正文触发复杂模式."""
    marker = "//" if c_style else "#"
    if marker in line:
        return line[: line.index(marker)]
    return line


def _strip_strings(code: str) -> str:
    r"""Strip double-quoted strings so ``"... for ..."`` does not fake a loop."""
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', code)


def _is_comment_only(stripped: str, c_style: bool) -> bool:
    """整行是否为注释."""
    if not c_style:
        return stripped.startswith("#")
    return stripped == "*/" or stripped.startswith(("//", "/*", "*"))


def _adjacent_comment_text(lines: list[str], index: int, c_style: bool) -> str | None:
    """同行尾注释，或紧邻上一非空注释行的正文；无则 None."""
    inline = _inline_comment_text(lines[index], c_style)
    if inline is not None:
        return inline
    prev = index - 1
    # 跳过空行：贴身注释允许空行间隔，避免误杀格式化结果。
    while prev >= 0 and not lines[prev].strip():
        prev -= 1
    if prev < 0 or not _is_comment_only(lines[prev].strip(), c_style):
        return None
    return lines[prev].strip()


def _inline_comment_text(raw: str, c_style: bool) -> str | None:
    """Extract trailing comment on a code line, if any."""
    if not c_style:
        if "#" not in raw or not raw[: raw.index("#")].strip():
            return None
        return raw[raw.index("#") :]
    if "//" in raw:
        return raw[raw.index("//") :]
    if "/*" not in raw:
        return None
    start = raw.index("/*")
    end = raw.find("*/", start)
    return raw[start : end + 2] if end >= 0 else None
