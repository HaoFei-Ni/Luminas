"""C/CUDA 自递归检测：eng-standard「非必要禁止递归」的数据源.

只认直接自调用 ``foo(... )``；间接互递归需人工/更重分析，本门禁不做。
"""

from __future__ import annotations

import re

_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def has_self_recursion(func_name: str, body_lines: list[str]) -> bool:
    """函数体在首个 ``{`` 之后是否出现对 ``func_name`` 的调用.

    跳过定义头：否则签名里的 ``func_name(`` 会被当成递归调用假阳性。
    """
    text = _strip_comments_and_strings("\n".join(body_lines))
    brace = text.find("{")
    if brace < 0:
        return False
    # 从花括号后扫描：只看可执行体。
    return any(match.group(1) == func_name for match in _CALL.finditer(text, brace + 1))


def _strip_comments_and_strings(text: str) -> str:
    """去掉 // 注释与粗粒度字符串，降低字面量里函数名误报."""
    lines: list[str] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for line in text.splitlines():
        if "//" in line:
            line = line[: line.index("//")]
        lines.append(re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", '""', line))
    return "\n".join(lines)
