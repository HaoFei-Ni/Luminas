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
def test_kv_roundtrip_identity(luma_native: Any) -> None:
    """Identity encode/decode stays within the 2-ulp L5 gate vs float64 view."""
    x = np.array([1.0, -2.5, 0.0, math.pi], dtype=np.float32)
    enc = np.asarray(luma_native.luma_kv_encode(x))
    dec = np.asarray(luma_native.luma_kv_decode(enc, x.size))
    ref64 = x.astype(np.float64)
    assert np.all(np.isfinite(dec))
    assert np.all(np.abs(dec.astype(np.float64) - ref64) <= ulp2_limit(ref64))


@pytest.mark.native
@pytest.mark.l2
def test_kv_decode_rejects_len_mismatch(luma_native: Any) -> None:
    """Decode must reject encoded length that does not match the requested n."""
    x = np.array([1.0, 2.0], dtype=np.float32)
    enc = np.asarray(luma_native.luma_kv_encode(x))
    with pytest.raises(RuntimeError, match="invalid argument"):
        luma_native.luma_kv_decode(enc, 3)
