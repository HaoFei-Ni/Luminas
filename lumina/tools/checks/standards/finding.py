"""Normalized finding records for L5 standard gates."""

from __future__ import annotations


def finding(target: str, issue: str, current: int = 0, limit: int = 1) -> dict[str, str]:
    """Build one normalized standard-gate finding."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }
