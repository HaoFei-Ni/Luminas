"""Unit tests for cognitive-complexity tier caps (L1–L5)."""

from __future__ import annotations

from tools.checks.python.cognitive_level import cognitive_level_cap, cognitive_level_violations


def test_l1_cap_is_five() -> None:
    """L1 maps to the complexipy Simple band (≤5)."""
    assert cognitive_level_cap("L1") == 5
    assert cognitive_level_cap("l1") == 5


def test_l1_rejects_threshold_above_cap() -> None:
    """Named L1 forbids max_cognitive_complexity > 5."""
    config = {"thresholds": {"cognitive_complexity_level": "L1", "max_cognitive_complexity": 8}}
    hits = cognitive_level_violations(config)
    assert len(hits) == 1
    assert hits[0]["limit"] == "5"


def test_l1_accepts_threshold_at_cap() -> None:
    """L1 with max=5 is valid."""
    config = {"thresholds": {"cognitive_complexity_level": "L1", "max_cognitive_complexity": 5}}
    assert cognitive_level_violations(config) == []


def test_unknown_level_is_rejected() -> None:
    """Typos in cognitive_complexity_level fail closed."""
    config = {"thresholds": {"cognitive_complexity_level": "L9", "max_cognitive_complexity": 5}}
    hits = cognitive_level_violations(config)
    assert hits and "未知" in hits[0]["issue"]


def test_empty_level_skips() -> None:
    """Unset cognitive_complexity_level emits no violations."""
    assert cognitive_level_violations({"thresholds": {}}) == []


def test_default_max_uses_cap() -> None:
    """Missing max_cognitive_complexity defaults to the tier cap."""
    config = {"thresholds": {"cognitive_complexity_level": "L2"}}
    assert cognitive_level_violations(config) == []
