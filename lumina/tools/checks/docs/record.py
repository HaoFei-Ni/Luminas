"""Shared violation record builder for document-quality checks."""

from __future__ import annotations


def violation(target: str, issue: str, current: int = 0, limit: int = 1) -> dict[str, str]:
    """Build one normalized document-gate finding."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }
