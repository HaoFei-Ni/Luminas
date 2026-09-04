"""Unit tests for LUM-ENG-101 professional naming heuristics."""

from __future__ import annotations

from tools.naming_rules import (
    check_c_symbol,
    check_include_guard,
    check_source_filename,
    check_symbol_file_coherence,
    is_forbidden_token,
)


def test_baseline_redundant_filename_flagged() -> None:
    """Under baseline/, filename must not repeat baseline (LUM-ENG-101 §3)."""
    issue = check_source_filename("kernel/baseline/luma_baseline_ternary.c")
    assert issue is not None
    assert "baseline" in issue.lower()


def test_clean_quant_filename_passes() -> None:
    """Canonical baseline quant file name is accepted."""
    assert check_source_filename("kernel/baseline/luma_quant_ternary.c") is None


def test_vague_util_filename_flagged() -> None:
    """Professional tier rejects vague util/defs stems."""
    assert check_source_filename("kernel/luma_cuda_util.h") is not None
    assert check_source_filename("kernel/baseline/luma_defs.h") is not None
    assert check_source_filename("kernel/luma_cuda_device.h") is None
    assert check_source_filename("kernel/baseline/luma_limits.h") is None


def test_pow2_token_forbidden() -> None:
    """Abbreviation policy: pow2 must be written power_of_two."""
    assert is_forbidden_token("luma_quant_block_pow2")
    assert check_c_symbol("luma_quant_block_pow2", "kernel/baseline/x.c") is not None
    assert check_c_symbol("luma_quant_power_of_two_encode", "kernel/baseline/x.c") is None
    assert not is_forbidden_token("luma_quant_power_of_two_encode")


def test_mxfp_token_forbidden() -> None:
    """Misleading mxfp token is always forbidden."""
    assert is_forbidden_token("luma_quant_mxfp_block")
    assert check_c_symbol("luma_quant_mxfp_block", "kernel/baseline/x.c") is not None


def test_layer_prefix_algorithm_rejects_quant() -> None:
    """algorithm/ symbols must be luma_kv_* (or allowlisted), not quant."""
    assert check_c_symbol("luma_quant_ternary_encode", "algorithm/luma_kv_codec.c") is not None
    assert check_c_symbol("luma_kv_encode_f32", "algorithm/luma_kv_codec.c") is None


def test_layer_prefix_and_action_order() -> None:
    """kernel layers accept svd/cuda; reject decode_fused / truncation / block_power_of_two."""
    assert check_c_symbol("luma_svd_truncate", "kernel/baseline/luma_svd_truncate.c") is None
    assert check_c_symbol("luma_cuda_kv_quant_int8", "kernel/cuda/luma_cuda_kv_quant_int8.cu") is None
    assert check_c_symbol("luma_cuda_fused_decode", "kernel/cuda/luma_cuda_fused_decode.cu") is None
    assert check_c_symbol("luma_cuda_decode_fused", "kernel/cuda/x.cu") is not None
    assert check_c_symbol("luma_svd_truncated", "kernel/baseline/x.c") is not None
    assert check_c_symbol("luma_quant_block_power_of_two", "kernel/baseline/x.c") is not None


def test_bad_dtype_suffix_flagged() -> None:
    """Dtype suffix must be lowercase f32/f64."""
    assert check_c_symbol("luma_kv_encode_F32", "algorithm/luma_kv_codec.c") is not None


def test_strerror_allowlisted() -> None:
    """luma_strerror is the canonical status helper name."""
    assert check_c_symbol("luma_strerror", "algorithm/luma_status.c") is None


def test_symbol_shape_requires_prefix_module_action() -> None:
    """Symbols need luma_ prefix, module+action arity, and no double underscore."""
    assert check_c_symbol("require_finite_f32", "algorithm/luma_kv_finite.c") is not None
    assert check_c_symbol("luma_kv__encode", "algorithm/luma_kv_codec.c") is not None
    assert check_c_symbol("luma_kv", "algorithm/luma_kv_codec.c") is not None


def test_include_guard_must_match_stem() -> None:
    """Header include guard must be LUMA_<STEM>_H."""
    bad = ["#ifndef LUMA_WRONG_H", "#define LUMA_WRONG_H", "#endif"]
    assert check_include_guard("kernel/luma_cuda_device.h", bad) is not None
    good = ["#ifndef LUMA_CUDA_DEVICE_H", "#define LUMA_CUDA_DEVICE_H", "#endif"]
    assert check_include_guard("kernel/luma_cuda_device.h", good) is None


def test_symbol_must_match_file_module() -> None:
    """Symbols in luma_quant_* files must stay under luma_quant_*."""
    assert check_symbol_file_coherence("luma_svd_truncate", "kernel/baseline/luma_quant_ternary.c") is not None
    assert (
        check_symbol_file_coherence(
            "luma_quant_ternary_encode",
            "kernel/baseline/luma_quant_ternary.c",
        )
        is None
    )
