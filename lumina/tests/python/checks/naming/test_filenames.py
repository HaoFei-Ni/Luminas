"""Unit tests for LUM-ENG-101 filename / token naming heuristics."""

from __future__ import annotations

from tools.checks.naming.rules import check_c_symbol, check_source_filename, is_forbidden_token


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
