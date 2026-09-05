"""Robustness L5 level and threshold-cap branch coverage."""

from __future__ import annotations

from tools.checks.robustness.caps import feature_ha_hits, threshold_cap_hits
from tools.checks.robustness.level import robustness_level_violations


def test_non_l5_skips_level() -> None:
    """Non-L5 robustness configs emit no switch findings."""
    assert robustness_level_violations({"robustness_standard": {"level": "L0"}}) == []


def test_l5_rejects_disabled_ha_switch() -> None:
    """L5 must keep require_ha_check on."""
    config = {
        "robustness_standard": {
            "level": "L5",
            "require_ha_check": False,
            "require_zero_unchecked_exceptions": True,
            "require_zero_none_risk": True,
            "require_global_state_cap": True,
            "require_boundary_tests": True,
        }
    }
    hits = robustness_level_violations(config)
    assert any("require_ha_check" in item["target"] for item in hits)


def test_l5_passes_when_complete() -> None:
    """All L5 robustness switches on yields no level hits."""
    config = {
        "robustness_standard": {
            "level": "L5",
            "require_ha_check": True,
            "require_zero_unchecked_exceptions": True,
            "require_zero_none_risk": True,
            "require_global_state_cap": True,
            "require_boundary_tests": True,
        }
    }
    assert robustness_level_violations(config) == []


def test_feature_and_threshold_caps() -> None:
    """Missing HA flag and loose thresholds are flagged."""
    standard = {
        "require_ha_check": True,
        "require_zero_unchecked_exceptions": True,
        "require_zero_none_risk": True,
        "require_global_state_cap": True,
        "max_unchecked_exception_paths": 0,
        "max_none_reference_risk": 0,
        "max_global_state_variables": 2,
    }
    config = {
        "features": {"enable_ha_check": False},
        "thresholds": {
            "max_unchecked_exception_paths": 3,
            "max_none_reference_risk": 1,
            "max_global_state_variables": 9,
        },
    }
    assert feature_ha_hits(config, standard)
    hits = threshold_cap_hits(config, standard)
    assert len(hits) == 3


def test_caps_pass_when_within_limit() -> None:
    """Tight thresholds and enable_ha_check pass."""
    standard = {
        "require_ha_check": True,
        "require_zero_unchecked_exceptions": True,
        "require_zero_none_risk": True,
        "require_global_state_cap": True,
        "max_unchecked_exception_paths": 0,
        "max_none_reference_risk": 0,
        "max_global_state_variables": 2,
    }
    config = {
        "features": {"enable_ha_check": True},
        "thresholds": {
            "max_unchecked_exception_paths": 0,
            "max_none_reference_risk": 0,
            "max_global_state_variables": 2,
        },
    }
    assert feature_ha_hits(config, standard) == []
    assert threshold_cap_hits(config, standard) == []


def test_disabled_cap_switches_skip() -> None:
    """Off switches skip feature/threshold enforcement."""
    standard = {
        "require_ha_check": False,
        "require_zero_unchecked_exceptions": False,
        "require_zero_none_risk": False,
        "require_global_state_cap": False,
    }
    config = {"features": {}, "thresholds": {}}
    assert feature_ha_hits(config, standard) == []
    assert threshold_cap_hits(config, standard) == []
