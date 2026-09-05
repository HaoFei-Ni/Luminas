"""Unit tests for naming-quality L5 config enforcement."""

from __future__ import annotations

from tools.checks.naming.level import naming_level_violations


def test_l5_rejects_disabled_filename_switch() -> None:
    """L5 level must keep require_filename_rules on."""
    config = {
        "naming_standard": {
            "level": "L5",
            "require_filename_rules": False,
            "require_symbol_rules": True,
            "require_macro_rules": True,
            "require_include_guard": True,
            "allow_baseline_macro_aliases": False,
        }
    }
    hits = naming_level_violations(config)
    assert any("require_filename_rules" in item["target"] for item in hits)


def test_l5_rejects_baseline_macro_aliases() -> None:
    """L5 forbids allow_baseline_macro_aliases=true."""
    config = {
        "naming_standard": {
            "level": "L5",
            "require_filename_rules": True,
            "require_symbol_rules": True,
            "require_macro_rules": True,
            "require_include_guard": True,
            "allow_baseline_macro_aliases": True,
        }
    }
    hits = naming_level_violations(config)
    assert any("allow_baseline_macro_aliases" in item["target"] for item in hits)


def test_l5_passes_when_complete() -> None:
    """Complete L5 naming switch set yields no level violations."""
    config = {
        "naming_standard": {
            "level": "L5",
            "require_filename_rules": True,
            "require_symbol_rules": True,
            "require_macro_rules": True,
            "require_include_guard": True,
            "allow_baseline_macro_aliases": False,
        }
    }
    assert naming_level_violations(config) == []


def test_non_l5_skips_enforcement() -> None:
    """Non-L5 naming configs emit no level findings."""
    config = {"naming_standard": {"level": "L0", "require_filename_rules": False}}
    assert naming_level_violations(config) == []
