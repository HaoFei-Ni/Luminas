"""Naming shape / token bans for LUM-ENG-101 professional tier."""

from __future__ import annotations

import re

_MIN_SYMBOL_PARTS = 3
_FORBIDDEN = re.compile(
    r"mxfp|\bluminas_|\bLumina|\bLUMINA_|_cla_|\bata\b|\baat\b|_cpu_"
    r"|\bpow2\b|_pow2_|^luma_.*pow2|pow2_"
    r"|_util(?:s)?(?:_|$)|_helper(?:s)?(?:_|$)|_common(?:_|$)|_misc(?:_|$)"
    r"|_tmp(?:_|$)|_temp(?:_|$)|_foo(?:_|$)|_bar(?:_|$)|_mgr(?:_|$)|_manager(?:_|$)"
    r"|(?:^|_)defs(?:_|$)|(?:^|_)util(?:s)?(?:_|$)",
    re.IGNORECASE,
)
_BAD_ORDER = re.compile(
    r"_decode_fused(?:_|$)|_encode_fused(?:_|$)|_quant_block_power_of_two(?:_|$)"
    r"|_block_power_of_two(?:_|$)|_svd_truncated(?:_|$)"
)
_BAD_DTYPE = re.compile(r"_(F32|F64|float|FLOAT|f32x)\b")
_SYMBOL_OK = re.compile(r"^luma_[a-z][a-z0-9_]*$")
_DOUBLE_US = re.compile(r"__")
_GENERIC_HEADERS = frozenset({"luma_kernels.h", "luma_cuda_kernels.h"})
VAGUE_STEMS = frozenset({"util", "utils", "helper", "helpers", "common", "misc", "defs", "tmp", "temp"})


def is_forbidden_token(name: str) -> bool:
    """Return True when name contains a banned misleading or vague token."""
    return _FORBIDDEN.search(name) is not None


def filename_issue(key: str, name: str, stem: str) -> str | None:
    """Filename professional checks as a single-return helper."""
    checks: list[tuple[bool, str]] = [
        (name in _GENERIC_HEADERS, f"废弃泛名头 {name}（§5 用 luma_<层>.h，如 luma_kernel.h）"),
        (not name.startswith("luma_"), f"源文件名缺少 luma_ 前缀: {name}"),
        (is_forbidden_token(stem), f"文件名含禁用/模糊词或未展开缩写: {name}"),
        (vague_stem_segment(stem), f"文件名含模糊段（禁止 util/defs/helper/…）: {name}"),
        ("baseline" in key.split("/") and "baseline" in stem, f"baseline/ 下禁止文件名重复 baseline: {name}"),
    ]
    # 单遍：首个命中即返回，避免多重 return 触发 PLR0911。
    for failed, message in checks:
        if failed:
            return message
    return None


def symbol_shape_issue(name: str) -> str | None:
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


def vague_stem_segment(stem: str) -> bool:
    """True when any snake segment is a vague professional ban."""
    return any(part in VAGUE_STEMS for part in stem.split("_"))
