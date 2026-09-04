"""Shared helpers for lumina Python tests (not collected as tests)."""

from __future__ import annotations

import numpy as np


def ulp2_limit(ref64: np.ndarray) -> np.ndarray:
    """Per-element 2-ulp FP32 gate vs an FP64 reference (eng-standard L5).

    Pass condition: ``|x - x64| <= 2 * 2^{-23} * max(1, |x64|)``.
    """
    scale = np.maximum(1.0, np.abs(ref64.astype(np.float64, copy=False)))
    return (2.0 * np.finfo(np.float32).eps) * scale
