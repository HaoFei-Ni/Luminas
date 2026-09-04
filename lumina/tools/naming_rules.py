"""LUM-ENG-101 命名 L4 启发式（纯规则，无 IO）.

档位：
- L0：符号/文件带 ``luma_`` / ``LUMA_`` 前缀。
- L4：层前缀对齐、禁用误导词、禁止 baseline 目录下文件名重复 baseline、
  dtype 后缀小写 ``f32``/``f64``。
"""

from __future__ import annotations

import re
from pathlib import Path

# 禁用误导性片段（LUM-ENG-101 §3）。
_FORBIDDEN = re.compile(
    r"mxfp|\bluminas_|\bLumina|\bLUMINA_|_cla_|\bata\b|\baat\b|_cpu_",
    re.IGNORECASE,
)

# 错误 dtype 后缀（允许 _f32/_f64 小写）。
_BAD_DTYPE = re.compile(r"_(F32|F64|float|FLOAT|f32x)\b")

_SYMBOL_OK = re.compile(r"^luma_[a-z][a-z0-9_]*$")

# 精确允许的非「模块_动作」形态。
_EXACT_ALLOW = frozenset({"luma_strerror"})

# 路径 → 允许的 luma_<module>_ 模块段（L4 层对齐）。
_LAYER_MODULES: list[tuple[str, frozenset[str]]] = [
    ("algorithm/", frozenset({"kv"})),
    ("kernel/baseline/", frozenset({"math", "quant", "svd", "cuda"})),
    ("kernel/", frozenset({"cuda", "kernel"})),
    ("wrapper/", frozenset({"bind", "cuda"})),
]

# 已废弃泛名（§5）；出现即违规。合法层头：luma_kernel.h / luma_cuda.h / luma_kv.h。
_GENERIC_HEADERS = frozenset({"luma_kernels.h", "luma_cuda_kernels.h"})


def is_forbidden_token(name: str) -> bool:
    """Return True when name contains a banned misleading token."""
    return _FORBIDDEN.search(name) is not None


def check_source_filename(file_key: str, *, file_allowlist: frozenset[str] | None = None) -> str | None:
    """Validate a source path key; return issue text or None."""
    key = file_key.replace("\\", "/")
    if file_allowlist and key in file_allowlist:
        return None
    name = Path(key).name
    stem = Path(key).stem
    if name in _GENERIC_HEADERS:
        return f"泛名头文件 {name}（§5 应用 luma_<层>.h）"
    if not name.startswith("luma_"):
        return f"源文件名缺少 luma_ 前缀: {name}"
    if is_forbidden_token(stem):
        return f"文件名含禁用误导词: {name}"
    parts = key.split("/")
    if "baseline" in parts and "baseline" in stem:
        return f"baseline/ 下禁止文件名重复 baseline: {name}"
    return None


def check_c_symbol(name: str, file_key: str) -> str | None:
    """Validate a C/CUDA function symbol against L4 naming rules."""
    if name in _EXACT_ALLOW:
        return None
    issue = _symbol_shape_issue(name)
    if issue:
        return issue
    allowed = _allowed_modules(file_key)
    if allowed is None:
        return None
    module = _module_of(name)
    if module in allowed:
        return None
    expect = "|".join(sorted(allowed))
    return f"层前缀不对齐（期望 luma_<{expect}>_*）: {name}"


def _symbol_shape_issue(name: str) -> str | None:
    """Prefix / banned-token / dtype / baseline shape checks."""
    if not _SYMBOL_OK.match(name):
        return f"符号须匹配 luma_[a-z][a-z0-9_]*: {name}"
    if is_forbidden_token(name):
        return f"符号含禁用误导词: {name}"
    if _BAD_DTYPE.search(name):
        return f"dtype 后缀须小写 f32/f64: {name}"
    if "baseline" in name:
        return f"符号禁止含 baseline（目录已表达角色）: {name}"
    return None


def _module_of(symbol: str) -> str:
    """Return the first path segment after ``luma_``."""
    rest = symbol[len("luma_") :]
    return rest.split("_", 1)[0]


def _allowed_modules(file_key: str) -> frozenset[str] | None:
    """Longest-prefix layer module set for file_key; None = no layer check."""
    key = file_key.replace("\\", "/")
    # 单遍：最长前缀优先，避免 algorithm 误套 kernel 模块表。
    for prefix, modules in _LAYER_MODULES:
        if key.startswith(prefix):
            return modules
    return None
