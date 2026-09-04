"""C/C++/CUDA 文档注释检测（lumina-eng-skill / LUM-ENG-101 §8）.

策略（只查 why 文档是否存在，不查文风）：
- 每个翻译单元必须以 ``/*`` 或 ``//`` 文件头 banner 开头；
- 每个函数*定义*前须有前置文档注释；
- 头文件每个导出原型前须有前置文档注释。
"""

from __future__ import annotations

from tools.checks.native.doc_comments_proto import prototype_at

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
    # 必须向上跳过空行：文档与原型之间允许空白分隔。
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
    # 必须单遍扫描：每段原型只判一次，结束行后跳过后续续行。
    while index < len(lines):
        hit, index = _prototype_doc_step(lines, index)
        if hit is not None:
            missing.append(hit)
    return missing


def _prototype_doc_step(
    lines: list[str],
    index: int,
) -> tuple[tuple[str, int] | None, int]:
    """Return ``((name, line), next_index)`` or ``(None, next_index)``."""
    stripped = lines[index].strip()
    if _skip_noise(stripped):
        return None, index + 1
    name, end = prototype_at(lines, index)
    if name is None or end is None:
        return None, index + 1
    if has_leading_doc_comment(lines, index + 1):
        return None, end + 1
    return (name, index + 1), end + 1


def _skip_noise(stripped: str) -> bool:
    """跳过空白、预处理、纯注释行（含 Doxygen ``*`` 续行）."""
    if not stripped or stripped in _NOISE_EXACT:
        return True
    return any(stripped.startswith(prefix) for prefix in _NOISE_PREFIXES)
