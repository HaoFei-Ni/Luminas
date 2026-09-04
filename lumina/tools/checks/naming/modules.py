"""Layer/module coherence helpers for LUM-ENG-101 naming."""

from __future__ import annotations

from pathlib import Path

from tools.checks.naming.shape import VAGUE_STEMS

_EXACT_ALLOW = frozenset({"luma_strerror"})
_UMBRELLA_STEMS = frozenset({"luma_kernel", "luma_limits"})
_LAYER_MODULES: list[tuple[str, frozenset[str]]] = [
    ("algorithm/", frozenset({"kv"})),
    ("kernel/baseline/", frozenset({"math", "quant", "svd", "limits"})),
    ("kernel/cuda/", frozenset({"cuda"})),
    ("kernel/", frozenset({"cuda", "kernel"})),
    ("wrapper/", frozenset({"bind", "cuda"})),
]


def check_symbol_file_coherence(name: str, file_key: str) -> str | None:
    """Symbols in an impl file must keep the file's module prefix."""
    if name in _EXACT_ALLOW:
        return None
    prefix = file_module_prefix(file_key)
    if prefix is None or name.startswith(prefix):
        return None
    return f"符号与文件模块不一致（期望 {prefix}*）: {name}"


def check_include_guard(file_key: str, lines: list[str]) -> str | None:
    """Header must define ``#ifndef/#define LUMA_<STEM>_H`` matching the filename."""
    key = file_key.replace("\\", "/")
    if Path(key).suffix.lower() not in {".h", ".cuh", ".hpp"}:
        return None
    expected = expected_include_guard(Path(key).stem)
    joined = "\n".join(lines[:40])
    if f"#ifndef {expected}" in joined and f"#define {expected}" in joined:
        return None
    return f"include guard 须为 {expected}"


def module_of(symbol: str) -> str:
    """Return the first path segment after ``luma_``."""
    return symbol[len("luma_") :].split("_", 1)[0]


def file_module_prefix(file_key: str) -> str | None:
    """``luma_quant_ternary.c`` → ``luma_quant_``; umbrella/macro-only → None."""
    stem = Path(file_key.replace("\\", "/")).stem
    if stem in _UMBRELLA_STEMS or not stem.startswith("luma_"):
        return None
    module = stem.split("_", 2)[1]
    if module in VAGUE_STEMS:
        return None
    return f"luma_{module}_"


def expected_include_guard(stem: str) -> str:
    """``luma_cuda_device`` → ``LUMA_CUDA_DEVICE_H``."""
    body = stem[5:] if stem.startswith("luma_") else stem
    return f"LUMA_{body.upper()}_H"


def allowed_modules(file_key: str) -> frozenset[str] | None:
    """Longest-prefix layer module set for file_key; None = no layer check."""
    key = file_key.replace("\\", "/")
    # 单遍：最长前缀优先，避免 algorithm 误套 kernel 模块表。
    for prefix, modules in _LAYER_MODULES:
        if key.startswith(prefix):
            return modules
    return None


def is_exact_allow(name: str) -> bool:
    """Return True for globally allowlisted symbol names."""
    return name in _EXACT_ALLOW
