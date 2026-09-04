"""L2: lossy baseline extension ``_luma_baseline`` (never the product path)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest


@pytest.mark.native
@pytest.mark.l2
def test_baseline_ternary_rejects_bad_threshold(luma_baseline: Any) -> None:
    """Ternary baseline must reject a negative threshold (documented L2)."""
    weights = np.array([1.0, 2.0], dtype=np.float32)
    with pytest.raises(RuntimeError, match="invalid argument"):
        luma_baseline.luma_quant_ternary_encode(weights, -0.1)
