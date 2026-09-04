"""Hypothesis property tests for candidate product KV RLE (``_luma_native``)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from helpers import ulp2_limit
from hypothesis import given, settings, strategies as st

pytest.importorskip("_luma_native")


def _finite_f32_arrays() -> st.SearchStrategy[np.ndarray]:
    """Finite float32 vectors; keep n modest for ha-profile wall clock."""
    values = st.floats(
        min_value=-1e6,
        max_value=1e6,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    )
    return st.lists(values, min_size=0, max_size=64).map(lambda xs: np.asarray(xs, dtype=np.float32))


@pytest.mark.native
@pytest.mark.l5
@given(x=_finite_f32_arrays())
@settings(deadline=None)
def test_kv_rle_roundtrip_within_2ulp(luma_native: Any, x: np.ndarray) -> None:
    """Encode/decode must stay within the 2-ulp gate vs float64 view."""
    enc = np.asarray(luma_native.luma_kv_encode(x))
    dec = np.asarray(luma_native.luma_kv_decode(enc, int(x.size)))
    ref64 = x.astype(np.float64)
    assert dec.shape == x.shape
    assert np.all(np.isfinite(dec))
    assert np.all(np.abs(dec.astype(np.float64) - ref64) <= ulp2_limit(ref64))


@pytest.mark.native
@pytest.mark.l2
@given(x=_finite_f32_arrays().filter(lambda arr: arr.size > 0))
@settings(deadline=None)
def test_kv_rle_enc_len_parity(luma_native: Any, x: np.ndarray) -> None:
    """RLE bitstream length is even and at most 2n floats."""
    enc = np.asarray(luma_native.luma_kv_encode(x))
    assert enc.size % 2 == 0
    assert enc.size <= x.size * 2
