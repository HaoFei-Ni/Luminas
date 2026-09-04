"""LUM-ENG-101 命名最高档启发式（纯规则，无 IO）.

专业约束（在 L4 层对齐之上）：
- 禁用模糊词（util/defs/helper/tmp…）与未展开缩写（pow2→power_of_two）；
- 符号至少 ``luma_<module>_<action…>``，禁止双下划线；
- 头文件 include guard 与文件名对齐；
- 实现文件内符号模块前缀与文件名模块一致。
"""

from __future__ import annotations

import re
from pathlib import Path

_MIN_SYMBOL_PARTS = 3  # luma + module + action

# 禁用误导 / 模糊 / 未展开缩写（LUM-ENG-101 §3 + 专业命名）。
_FORBIDDEN = re.compile(
    r"mxfp|\bluminas_|\bLumina|\bLUMINA_|_cla_|\bata\b|\baat\b|_cpu_"
    r"|\bpow2\b|_pow2_|^luma_.*pow2|pow2_"
    r"|_util(?:s)?(?:_|$)|_helper(?:s)?(?:_|$)|_common(?:_|$)|_misc(?:_|$)"
    r"|_tmp(?:_|$)|_temp(?:_|$)|_foo(?:_|$)|_bar(?:_|$)|_mgr(?:_|$)|_manager(?:_|$)"
    r"|(?:^|_)defs(?:_|$)|(?:^|_)util(?:s)?(?:_|$)",
    re.IGNORECASE,
)

# 专业语序：禁止「动作_修饰」颠倒与缺动作名词串。
_BAD_ORDER = re.compile(
    r"_decode_fused(?:_|$)|_encode_fused(?:_|$)|_quant_block_power_of_two(?:_|$)"
    r"|_block_power_of_two(?:_|$)|_svd_truncated(?:_|$)"
)
_BAD_DTYPE = re.compile(r"_(F32|F64|float|FLOAT|f32x)\b")
_SYMBOL_OK = re.compile(r"^luma_[a-z][a-z0-9_]*$")
_DOUBLE_US = re.compile(r"__")
_EXACT_ALLOW = frozenset({"luma_strerror"})
_UMBRELLA_STEMS = frozenset({"luma_kernel", "luma_limits"})

_LAYER_MODULES: list[tuple[str, frozenset[str]]] = [
    ("algorithm/", frozenset({"kv"})),
    ("kernel/baseline/", frozenset({"math", "quant", "svd", "limits"})),
    ("kernel/cuda/", frozenset({"cuda"})),
    ("kernel/", frozenset({"cuda", "kernel"})),
    ("wrapper/", frozenset({"bind", "cuda"})),
]

_GENERIC_HEADERS = frozenset({"luma_kernels.h", "luma_cuda_kernels.h"})
_VAGUE_STEMS = frozenset({"util", "utils", "helper", "helpers", "common", "misc", "defs", "tmp", "temp"})


def is_forbidden_token(name: str) -> bool:
    """Return True when name contains a banned misleading or vague token."""
    return _FORBIDDEN.search(name) is not None


def check_source_filename(file_key: str, *, file_allowlist: frozenset[str] | None = None) -> str | None:
    """Validate a source path key; return issue text or None."""
    key = file_key.replace("\\", "/")
    if file_allowlist and key in file_allowlist:
        return None
    name = Path(key).name
    stem = Path(key).stem
    return _filename_issue(key, name, stem)


def check_c_symbol(name: str, file_key: str) -> str | None:
    """Validate a C/CUDA function symbol against professional naming rules."""
    if name in _EXACT_ALLOW:
        return None
    issue = _symbol_shape_issue(name) or check_symbol_file_coherence(name, file_key)
    if issue:
        return issue
    allowed = _allowed_modules(file_key)
    if allowed is None or _module_of(name) in allowed:
        return None
    expect = "|".join(sorted(allowed))
    return f"层前缀不对齐（期望 luma_<{expect}>_*）: {name}"


def check_symbol_file_coherence(name: str, file_key: str) -> str | None:
    """Symbols in an impl file must keep the file's module prefix."""
    if name in _EXACT_ALLOW:
        return None
    prefix = _file_module_prefix(file_key)
    if prefix is None or name.startswith(prefix):
        return None
    return f"符号与文件模块不一致（期望 {prefix}*）: {name}"


def check_include_guard(file_key: str, lines: list[str]) -> str | None:
    """Header must define ``#ifndef/#define LUMA_<STEM>_H`` matching the filename."""
    key = file_key.replace("\\", "/")
    if Path(key).suffix.lower() not in {".h", ".cuh", ".hpp"}:
        return None
    expected = _expected_include_guard(Path(key).stem)
    joined = "\n".join(lines[:40])
    if f"#ifndef {expected}" in joined and f"#define {expected}" in joined:
        return None
    return f"include guard 须为 {expected}"


def _filename_issue(key: str, name: str, stem: str) -> str | None:
    """Filename professional checks as a single-return helper."""
    checks: list[tuple[bool, str]] = [
        (name in _GENERIC_HEADERS, f"废弃泛名头 {name}（§5 用 luma_<层>.h，如 luma_kernel.h）"),
        (not name.startswith("luma_"), f"源文件名缺少 luma_ 前缀: {name}"),
        (is_forbidden_token(stem), f"文件名含禁用/模糊词或未展开缩写: {name}"),
        (_vague_stem_segment(stem), f"文件名含模糊段（禁止 util/defs/helper/…）: {name}"),
        ("baseline" in key.split("/") and "baseline" in stem, f"baseline/ 下禁止文件名重复 baseline: {name}"),
    ]
    # 单遍：首个命中即返回，避免多重 return 触发 PLR0911。
    for failed, message in checks:
        if failed:
            return message
    return None


def _symbol_shape_issue(name: str) -> str | None:
    """Prefix / banned-token / dtype / baseline / arity shape checks."""
    checks: list[tuple[bool, str]] = [
        (not bool(_SYMBOL_OK.match(name)), f"符号须匹配 luma_[a-z][a-z0-9_]*: {name}"),
        (bool(_DOUBLE_US.search(name) or name.endswith("_")), f"符号禁止双下划线或尾部下划线: {name}"),
        (is_forbidden_token(name), f"符号含禁用/模糊词或未展开缩写: {name}"),
        (bool(_BAD_DTYPE.search(name)), f"dtype 后缀须小写 f32/f64: {name}"),
        (bool(_BAD_ORDER.search(name)), f"符号语序不专业（须 module_[algo]_action，禁 decode_fused/缺动作）: {name}"),
        ("baseline" in name, f"符号禁止含 baseline（目录已表达角色）: {name}"),
        (len(name.split("_")) < _MIN_SYMBOL_PARTS, f"符号须含模块与动作（luma_<module>_<action…>）: {name}"),
    ]
    # 单遍：首个命中即返回，避免多重 return 触发 PLR0911。
    for failed, message in checks:
        if failed:
            return message
    return None


def _vague_stem_segment(stem: str) -> bool:
    """True when any snake segment is a vague professional ban."""
    return any(part in _VAGUE_STEMS for part in stem.split("_"))


def _module_of(symbol: str) -> str:
    """Return the first path segment after ``luma_``."""
    return symbol[len("luma_") :].split("_", 1)[0]


def _file_module_prefix(file_key: str) -> str | None:
    """``luma_quant_ternary.c`` → ``luma_quant_``; umbrella/macro-only → None."""
    stem = Path(file_key.replace("\\", "/")).stem
    if stem in _UMBRELLA_STEMS or not stem.startswith("luma_"):
        return None
    module = stem.split("_", 2)[1]
    if module in _VAGUE_STEMS:
        return None
    return f"luma_{module}_"


def _expected_include_guard(stem: str) -> str:
    """``luma_cuda_device`` → ``LUMA_CUDA_DEVICE_H``."""
    body = stem[5:] if stem.startswith("luma_") else stem
    return f"LUMA_{body.upper()}_H"


def _allowed_modules(file_key: str) -> frozenset[str] | None:
    """Longest-prefix layer module set for file_key; None = no layer check."""
    key = file_key.replace("\\", "/")
    # 单遍：最长前缀优先，避免 algorithm 误套 kernel 模块表。
    for prefix, modules in _LAYER_MODULES:
        if key.startswith(prefix):
            return modules
    return None
