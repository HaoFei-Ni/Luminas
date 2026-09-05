"""L4/L5 endurance: repeated product KV encode/decode fatigue rounds."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from helpers import ulp2_limit

# L5 长稳：最少疲劳轮次（与 quality-gate.toml endurance_standard.min_fatigue_rounds 对齐）
FATIGUE_ROUNDS = 100


@pytest.mark.native
@pytest.mark.l4
@pytest.mark.endurance
def test_kv_rle_fatigue_rounds(luma_native: Any) -> None:
    """Repeated encode/decode must stay finite and within 2-ulp (fatigue)."""
    x = np.array([1.0, -2.5, 0.0, 3.25, 1.0], dtype=np.float32)
    ref64 = x.astype(np.float64)
    # 必须跑满 FATIGUE_ROUNDS：短跑无法暴露泄漏/漂移类疲劳问题。
    for _ in range(FATIGUE_ROUNDS):
        enc = np.asarray(luma_native.luma_kv_encode(x))
        dec = np.asarray(luma_native.luma_kv_decode(enc, int(x.size)))
        assert np.all(np.isfinite(dec))
        assert np.all(np.abs(dec.astype(np.float64) - ref64) <= ulp2_limit(ref64))
