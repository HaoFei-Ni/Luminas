"""Unit tests for HA exception / global / None-risk metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tools.ha_except import unchecked_exception_paths
from tools.ha_gate import ha_violations
from tools.ha_globals import max_global_state
from tools.ha_none import none_reference_risk
from tools.hypothesis_profiles import profile_settings_kwargs

if TYPE_CHECKING:
    from pathlib import Path


def test_silent_except_counts_as_unchecked(tmp_path: Path) -> None:
    """Bare or pass-only except handlers increment unchecked paths."""
    path = tmp_path / "bad.py"
    path.write_text("def f():\n    try:\n        1\n    except Exception:\n        pass\n", encoding="utf-8")
    count, _ = unchecked_exception_paths([("tools/bad.py", path)])
    assert count == 1


def test_mutable_module_dict_counts_as_global_state(tmp_path: Path) -> None:
    """Module-level ``{}`` is mutable global state."""
    path = tmp_path / "state.py"
    path.write_text("_CACHE = {}\n", encoding="utf-8")
    count, _ = max_global_state([("tools/state.py", path)])
    assert count == 1


def test_optional_attr_without_guard_is_none_risk(tmp_path: Path) -> None:
    """Optional param attribute access without None check is a risk."""
    path = tmp_path / "opt.py"
    path.write_text("def f(x: str | None) -> int:\n    return len(x.strip())\n", encoding="utf-8")
    count, _ = none_reference_risk([("tools/opt.py", path)])
    assert count >= 1


def test_optional_with_none_guard_is_clean(tmp_path: Path) -> None:
    """``if x is None`` before use clears None-reference risk."""
    path = tmp_path / "ok.py"
    path.write_text(
        "def f(x: str | None) -> int:\n    if x is None:\n        return 0\n    return len(x.strip())\n",
        encoding="utf-8",
    )
    count, _ = none_reference_risk([("tools/ok.py", path)])
    assert count == 0


def test_ha_feature_flag_disables_checks() -> None:
    """Disabled HA check returns no violations."""
    assert ha_violations({"features": {"enable_ha_check": False}, "thresholds": {}}) == []


def test_ha_profile_maps_stateful_and_health_check() -> None:
    """HA profile keys map into Hypothesis settings kwargs."""
    raw = {
        "max_examples": 5000,
        "deadline_ms": 60000,
        "print_blob": True,
        "derandomize": True,
        "persist_examples": True,
        "stateful_step_count": 200,
        "suppress_health_check": False,
        "max_examples_per_run": 1000,
    }
    kwargs = profile_settings_kwargs(raw, database_factory=lambda: "db")
    assert kwargs["max_examples"] == 5000
    assert kwargs["deadline"] == 60000
    assert kwargs["stateful_step_count"] == 200
    assert kwargs["suppress_health_check"] == ()
    assert "database" not in kwargs
    assert "max_examples_per_run" not in kwargs
