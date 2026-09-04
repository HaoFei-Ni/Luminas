"""Unit tests for LUM-ENG-101 naming L4 heuristics."""

from __future__ import annotations

from tools.naming_rules import (
    check_c_symbol,
    check_source_filename,
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


def test_mxfp_token_forbidden() -> None:
    """Misleading mxfp token is always forbidden."""
    assert is_forbidden_token("luma_quant_mxfp_block")
    assert check_c_symbol("luma_quant_mxfp_block", "kernel/baseline/x.c") is not None


def test_layer_prefix_algorithm_rejects_quant() -> None:
    """algorithm/ symbols must be luma_kv_* (or allowlisted), not quant."""
    assert check_c_symbol("luma_quant_ternary_encode", "algorithm/luma_kv_codec.c") is not None
    assert check_c_symbol("luma_kv_encode_f32", "algorithm/luma_kv_codec.c") is None


def test_layer_prefix_kernel_accepts_svd_cuda() -> None:
    """kernel/baseline allows math/quant/svd/cuda modules."""
    assert check_c_symbol("luma_svd_truncated", "kernel/baseline/luma_svd_truncated.c") is None
    assert check_c_symbol("luma_cuda_kv_quant_int8", "kernel/baseline/luma_cuda_kv_quant_int8.cu") is None


def test_bad_dtype_suffix_flagged() -> None:
    """Dtype suffix must be lowercase f32/f64."""
    assert check_c_symbol("luma_kv_encode_F32", "algorithm/luma_kv_codec.c") is not None


def test_strerror_allowlisted() -> None:
    """luma_strerror is the canonical status helper name."""
    assert check_c_symbol("luma_strerror", "algorithm/luma_status.c") is None


def test_missing_luma_prefix_flagged() -> None:
    """Exported/static C symbols must use luma_ prefix."""
    assert check_c_symbol("require_finite_f32", "algorithm/luma_kv_finite.c") is not None
