"""Robustness boundary-test and gate CLI branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.robustness import gate as rob_gate
from tools.checks.robustness.boundary import boundary_test_hits


def test_disabled_returns_empty(tmp_path: Path) -> None:
    """enable=false short-circuits robustness_violations."""
    assert rob_gate.robustness_violations({"robustness_standard": {"enable": False}}, root=tmp_path) == []


def test_missing_and_markerless_boundary(tmp_path: Path) -> None:
    """Absent files and files without L2 markers are flagged."""
    bare = tmp_path / "bare.c"
    bare.write_text("int main(void){return 0;}\n", encoding="utf-8")
    standard = {
        "require_boundary_tests": True,
        "boundary_files": ["missing.c", "bare.c"],
        "boundary_markers": ["L2", "ERR_ARG"],
    }
    hits = boundary_test_hits(tmp_path, standard)
    assert any("缺少" in item["issue"] for item in hits)
    assert any("线索" in item["issue"] for item in hits)


def test_boundary_pass_and_switch_off(tmp_path: Path) -> None:
    """Marked file passes; disabled switch yields no hits."""
    path = tmp_path / "ok.c"
    path.write_text("/* L2 */ ERR_ARG\n", encoding="utf-8")
    on = {
        "require_boundary_tests": True,
        "boundary_files": ["ok.c"],
        "boundary_markers": ["L2"],
    }
    assert boundary_test_hits(tmp_path, on) == []
    assert boundary_test_hits(tmp_path, {"require_boundary_tests": False}) == []


def test_full_config_pass(tmp_path: Path) -> None:
    """Complete L5 robustness config against a mini tree passes."""
    path = tmp_path / "tests" / "c"
    path.mkdir(parents=True)
    (path / "test_luma_kv.c").write_text("/* L2 */ LUMA_ERR_ARG\n", encoding="utf-8")
    config = {
        "robustness_standard": {
            "enable": True,
            "level": "L5",
            "require_ha_check": True,
            "require_zero_unchecked_exceptions": True,
            "require_zero_none_risk": True,
            "require_global_state_cap": True,
            "require_boundary_tests": True,
            "max_unchecked_exception_paths": 0,
            "max_none_reference_risk": 0,
            "max_global_state_variables": 2,
            "boundary_files": ["tests/c/test_luma_kv.c"],
            "boundary_markers": ["L2", "ERR_ARG"],
        },
        "features": {"enable_ha_check": True},
        "thresholds": {
            "max_unchecked_exception_paths": 0,
            "max_none_reference_risk": 0,
            "max_global_state_variables": 2,
        },
    }
    assert rob_gate.robustness_violations(config, root=tmp_path) == []


def test_main_paths(monkeypatch: Any) -> None:
    """main covers skip / pass / fail exits."""
    monkeypatch.setattr(rob_gate, "load_config", lambda: {"robustness_standard": {"enable": False}})
    assert rob_gate.main() == 0
    monkeypatch.setattr(rob_gate, "load_config", lambda: {"robustness_standard": {"enable": True}})
    monkeypatch.setattr(rob_gate, "robustness_violations", lambda _c: [])
    assert rob_gate.main() == 0
    monkeypatch.setattr(
        rob_gate,
        "robustness_violations",
        lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
    )
    assert rob_gate.main() == 1
