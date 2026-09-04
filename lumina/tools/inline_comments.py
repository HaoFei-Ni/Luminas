"""复杂语句行内注释检测（C/Python 共用启发式）.

LUM-ENG-101 §8：循环、同步点、关键数值原语行须有贴身 why 注释。
本模块只报告「缺注释 / why 不合格的复杂行」；是否判失败由门禁开关决定。

档位：
- L0（默认）：复杂行邻接有 ``//`` / ``#`` / 块注释即通过。
- L4（``require_why=True``）：邻接注释须命中 why 线索，且不得是 what 模板句。
"""

from __future__ import annotations

import re

from tools.inline_comment_scan import scan_uncommented
from tools.inline_why import is_why_comment

# C/CUDA：循环、同步、原子、共享内存、数值不稳定点（L2 扩模式）。
_C_COMPLEX = re.compile(
    r"\b(for|while|do)\b"
    r"|__syncthreads\b"
    r"|__shared__\b"
    r"|atomic(?:Add|Exch|CAS|Max|Min)\b"
    r"|\bfrexpf?\s*\("
    r"|\bldexpf?\s*\("
    r"|exp2f\s*\("
    r"|floorf\s*\(\s*log2"
)

# Python：仅循环头（与 AST For/While 互补；字符串扫描用于无 AST 的片段）。
_PY_COMPLEX = re.compile(r"^\s*(async\s+)?(for|while)\b")

__all__ = [
    "is_why_comment",
    "uncommented_complex_c_lines",
    "uncommented_complex_py_lines",
]


def uncommented_complex_c_lines(body_lines: list[str], *, require_why: bool = False) -> list[int]:
    """返回函数体内缺行内注释（或 why 不合格）的复杂语句行号（1-based）."""
    return scan_uncommented(body_lines, _C_COMPLEX, c_style=True, require_why=require_why)


def uncommented_complex_py_lines(body_lines: list[str], *, require_why: bool = False) -> list[int]:
    """返回 Python 片段中缺 ``#``（或 why 不合格）的循环行号（1-based）."""
    return scan_uncommented(body_lines, _PY_COMPLEX, c_style=False, require_why=require_why)
