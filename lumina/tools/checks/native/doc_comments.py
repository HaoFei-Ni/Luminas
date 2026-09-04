"""C/C++/CUDA 文档注释检测（lumina-eng-skill / LUM-ENG-101 §8）.

策略（只查 why 文档是否存在，不查文风）：
- 每个翻译单元必须以 ``/*`` 或 ``//`` 文件头 banner 开头；
- 每个函数*定义*前须有前置文档注释；
- 头文件每个导出原型前须有前置文档注释。
"""

from __future__ import annotations

import re

_FUNC_PROTO = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*;"
)
_CONTROL = frozenset({"if", "for", "while", "switch", "do", "return"})
_NOISE_EXACT = frozenset({"*/", 'extern "C" {', 'extern "C"{'})
_NOISE_PREFIXES = (
    "#",
    "//",
    "/*",
    "*",
    "{",
    "}",
    "namespace",
    "using ",
    "typedef",
    "struct",
    "enum",
    "class",
)


def has_file_banner(lines: list[str]) -> bool:
    """文件去 BOM/前导空白后是否以块注释或行注释开头."""
    text = "\n".join(lines).lstrip("\ufeff").lstrip()
    return text.startswith("/*") or text.startswith("//")


def has_leading_doc_comment(lines: list[str], start_line: int) -> bool:
    """``start_line``（1-based）紧上方是否为文档注释（允许中间空行）."""
    index = start_line - 2
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    while index >= 0 and not lines[index].strip():
        index -= 1
    if index < 0:
        return False
    stripped = lines[index].strip()
    if stripped.startswith("//"):
        return True
    # 多行 /* ... */ 的最后一行通常是 ``*/`` 或 ``* ... */``。
    return stripped.endswith("*/")


def undocumented_prototypes(lines: list[str]) -> list[tuple[str, int]]:
    """返回头文件中缺少前置文档的原型 ``(name, line)``."""
    missing: list[tuple[str, int]] = []
    index = 0
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
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
        # 跳到原型结束行之后，避免同一声明被窗口重复命中。
        index = end + 1
    return missing


def _skip_noise(stripped: str) -> bool:
    """跳过空白、预处理、纯注释行（含 Doxygen ``*`` 续行）."""
    if not stripped or stripped in _NOISE_EXACT:
        return True
    return any(stripped.startswith(prefix) for prefix in _NOISE_PREFIXES)


def _prototype_at(lines: list[str], start: int) -> tuple[str | None, int | None]:
    """若 ``start`` 起是 ``name(...);`` 原型，返回名字与结束行下标."""
    window: list[str] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for index in range(start, min(start + 12, len(lines))):
        window.append(lines[index].rstrip())
        joined = " ".join(part.strip() for part in window)
        done, name = _proto_step(joined)
        if done:
            return (name, index) if name else (None, None)
    return None, None


def _proto_step(joined: str) -> tuple[bool, str | None]:
    """Return (done, name); done means stop widening the prototype window."""
    if "{" in joined:
        return True, None
    if ";" not in joined:
        return False, None
    return True, _parse_proto_window(joined)


def _parse_proto_window(joined: str) -> str | None:
    """Return prototype name from a joined window that already contains ``;``."""
    match = _FUNC_PROTO.search(joined)
    if match is None:
        return None
    name = match.group(1)
    return None if name in _CONTROL else name
