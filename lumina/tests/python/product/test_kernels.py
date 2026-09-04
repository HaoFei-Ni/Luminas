"""L2 / L3 / L5: product ``_luma_native`` bind agrees with algorithm when built.

纯 Python 环境无扩展时，本模块用例全部 skip；有损基线见 ``test_baselines.py``。
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from helpers import ulp2_limit


@pytest.mark.native
@pytest.mark.l3
@pytest.mark.l5
def test_kv_roundtrip_rle(luma_native: Any) -> None:
    """RLE encode/decode stays within the 2-ulp L5 gate vs float64 view."""
    x = np.array([1.0, -2.5, 0.0, math.pi], dtype=np.float32)
    enc = np.asarray(luma_native.luma_kv_encode(x))
    dec = np.asarray(luma_native.luma_kv_decode(enc, x.size))
    ref64 = x.astype(np.float64)
    assert enc.size == 8
    assert np.all(np.isfinite(dec))
    assert np.all(np.abs(dec.astype(np.float64) - ref64) <= ulp2_limit(ref64))


@pytest.mark.native
@pytest.mark.l3
def test_kv_rle_shortens_runs(luma_native: Any) -> None:
    """Repeated values must compress below the 2n worst-case bitstream."""
    x = np.array([1.0, 1.0, 1.0, 2.0, 2.0], dtype=np.float32)
    enc = np.asarray(luma_native.luma_kv_encode(x))
    assert enc.size == 4
    dec = np.asarray(luma_native.luma_kv_decode(enc, x.size))
    assert np.array_equal(dec, x)


@pytest.mark.native
@pytest.mark.l2
def test_kv_decode_rejects_len_mismatch(luma_native: Any) -> None:
    """Decode must reject encoded streams that do not expand to n."""
    x = np.array([1.0, 2.0], dtype=np.float32)
    enc = np.asarray(luma_native.luma_kv_encode(x))
    with pytest.raises(RuntimeError, match="invalid argument"):
        luma_native.luma_kv_decode(enc, 3)
