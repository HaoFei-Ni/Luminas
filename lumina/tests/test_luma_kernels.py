"""L3: bind + kernel agree when the extension is built."""

from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")
_luma_native = pytest.importorskip("_luma_native")


def test_kv_roundtrip_identity() -> None:
    x = np.array([1.0, -2.5, 0.0, math.pi], dtype=np.float32)
    enc = np.asarray(_luma_native.kv_encode(x))
    dec = np.asarray(_luma_native.kv_decode(enc, x.size))
    lim = 2 * np.finfo(np.float32).eps * np.maximum(1.0, np.abs(x.astype(np.float64)))
    assert np.all(np.abs(dec.astype(np.float64) - x.astype(np.float64)) <= lim)


def test_kv_decode_rejects_len_mismatch() -> None:
    x = np.array([1.0, 2.0], dtype=np.float32)
    enc = np.asarray(_luma_native.kv_encode(x))
    with pytest.raises(RuntimeError, match="invalid argument"):
        _luma_native.kv_decode(enc, 3)


def test_baseline_ternary_rejects_bad_threshold() -> None:
    w = np.array([1.0, 2.0], dtype=np.float32)
    with pytest.raises(RuntimeError, match="invalid argument"):
        _luma_native.baseline_ternary_encode(w, -0.1)
