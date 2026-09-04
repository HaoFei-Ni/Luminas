"""CUDA baseline smoke tests (``@cuda``); skip when ``_luma_cuda`` is absent."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest


@pytest.mark.cuda
@pytest.mark.l2
def test_cuda_kv_quant_int8_smoke(luma_cuda: Any) -> None:
    """Lossy int8 baseline must accept a finite host buffer and return scales/codes."""
    x = np.linspace(-1.0, 1.0, 256, dtype=np.float32)
    scales, codes = luma_cuda.luma_cuda_kv_quant_int8(x, block_size=32, threads_per_block=128)
    assert scales.size > 0
    assert codes.shape == x.shape
    assert codes.dtype == np.int8


@pytest.mark.cuda
@pytest.mark.l2
def test_cuda_kv_quant_rejects_bad_block(luma_cuda: Any) -> None:
    """CUDA baseline must reject non-positive block_size."""
    x = np.ones(8, dtype=np.float32)
    with pytest.raises(RuntimeError):
        luma_cuda.luma_cuda_kv_quant_int8(x, block_size=0, threads_per_block=128)
