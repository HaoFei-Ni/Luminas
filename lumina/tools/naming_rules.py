"""LUM-ENG-101 命名最高档启发式（纯规则，无 IO）.

专业约束（在 L4 层对齐之上）：
- 禁用模糊词（util/defs/helper/tmp…）与未展开缩写（pow2→power_of_two）；
- 符号至少 ``luma_<module>_<action…>``，禁止双下划线；
- 头文件 include guard 与文件名对齐；
- 实现文件内符号模块前缀与文件名模块一致。
"""

from __future__ import annotations

from pathlib import Path

from tools.naming_modules import (
    allowed_modules,
    check_include_guard,
    check_symbol_file_coherence,
    is_exact_allow,
    module_of,
)
from tools.naming_shape import filename_issue, is_forbidden_token, symbol_shape_issue

__all__ = [
    "check_c_symbol",
    "check_include_guard",
    "check_source_filename",
    "check_symbol_file_coherence",
    "is_forbidden_token",
]


def check_source_filename(file_key: str, *, file_allowlist: frozenset[str] | None = None) -> str | None:
    """Validate a source path key; return issue text or None."""
    key = file_key.replace("\\", "/")
    if file_allowlist and key in file_allowlist:
        return None
    name = Path(key).name
    stem = Path(key).stem
    return filename_issue(key, name, stem)


def check_c_symbol(name: str, file_key: str) -> str | None:
    """Validate a C/CUDA function symbol against professional naming rules."""
    if is_exact_allow(name):
        return None
    issue = symbol_shape_issue(name) or check_symbol_file_coherence(name, file_key)
    if issue:
        return issue
    allowed = allowed_modules(file_key)
    if allowed is None or module_of(name) in allowed:
        return None
    expect = "|".join(sorted(allowed))
    return f"层前缀不对齐（期望 luma_<{expect}>_*）: {name}"
