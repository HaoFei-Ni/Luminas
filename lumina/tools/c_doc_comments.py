"""C/C++/CUDA 文档注释检测（eng-standard / LUM-ENG-101 §8）.

策略（只查 why 文档是否存在，不查文风）：
- 每个翻译单元必须以 ``/*`` 或 ``//`` 文件头 banner 开头；
- 每个函数*定义*前须有前置文档注释；
- 头文件每个导出原型前须有前置文档注释。

为何不强制解析 Doxygen 标签：门禁要稳、要快；缺注释即违规，标签完整性交给评审。
"""

from __future__ import annotations

import re

# 允许 CUDA/C++ 限定词前缀；捕获名后必须是 ``(...);`` 原型而非定义。
_FUNC_PROTO = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*;"
)
# 控制关键字误匹配时直接丢弃（``if (...);`` 极少见但仍防护）。
_CONTROL = frozenset({"if", "for", "while", "switch", "do", "return"})


def has_file_banner(lines: list[str]) -> bool:
    """文件去 BOM/前导空白后是否以块注释或行注释开头."""
    text = "\n".join(lines).lstrip("\ufeff").lstrip()
    return text.startswith("/*") or text.startswith("//")


def has_leading_doc_comment(lines: list[str], start_line: int) -> bool:
    """``start_line``（1-based）紧上方是否为文档注释（允许中间空行）.

    接受 ``//`` 或以上一行以 ``*/`` 结束的块注释；不要求 @brief 关键字。
    """
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
    """跳过空白、预处理、纯注释行（含 Doxygen ``*`` 续行）.

    若不跳过 ``* O(n) ...``，后续窗口里的 ``{`` 会把 ``O`` 误解析成函数名。
    """
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
    """若 ``start`` 起是 ``name(...);`` 原型，返回名字与结束行下标.

    窗口内出现 ``{`` 视为定义而非原型，返回 None（定义由 metrics 侧管）。
    """
    window: list[str] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
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
