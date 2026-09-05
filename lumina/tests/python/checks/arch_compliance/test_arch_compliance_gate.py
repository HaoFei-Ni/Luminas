"""Architecture-compliance L5 gate branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.arch_compliance import gate as arch_gate


def test_disabled_returns_empty(tmp_path: Path) -> None:
    """enable=false short-circuits."""
    assert (
        arch_gate.architecture_compliance_violations({"architecture_standard": {"enable": False}}, root=tmp_path) == []
    )


def test_full_config_pass(tmp_path: Path) -> None:
    """Complete L5 architecture config against a mini tree passes."""
    path = tmp_path / "tests" / "python" / "checks" / "architecture"
    path.mkdir(parents=True)
    (path / "test_import_graph.py").write_text("cycle fan_out inheritance duplication\n", encoding="utf-8")
    config = {
        "architecture_standard": {
            "enable": True,
            "level": "L5",
            "require_architecture_check": True,
            "require_zero_cycles": True,
            "require_fan_out_cap": True,
            "require_inheritance_cap": True,
            "require_clone_cap": True,
            "require_architecture_tests": True,
            "max_cyclic_dependencies": 0,
            "max_module_fan_out": 8,
            "max_inheritance_depth": 4,
            "max_duplicate_code_blocks": 0,
            "architecture_test_files": ["tests/python/checks/architecture/test_import_graph.py"],
            "architecture_test_markers": ["cycle", "fan_out", "inheritance", "duplication"],
        },
        "features": {"enable_architecture_check": True},
        "thresholds": {
            "max_cyclic_dependencies": 0,
            "max_module_fan_out": 8,
            "max_inheritance_depth": 4,
            "max_duplicate_code_blocks": 0,
        },
    }
    assert arch_gate.architecture_compliance_violations(config, root=tmp_path) == []


def test_main_paths(monkeypatch: Any) -> None:
    """main covers skip / pass / fail via shared stage runner."""
    monkeypatch.setattr(arch_gate, "load_config", lambda: {"architecture_standard": {"enable": False}})
    assert arch_gate.main() == 0
    monkeypatch.setattr(arch_gate, "load_config", lambda: {"architecture_standard": {"enable": True}})
    monkeypatch.setattr(arch_gate, "architecture_compliance_violations", lambda _c: [])
    assert arch_gate.main() == 0
    monkeypatch.setattr(
        arch_gate,
        "architecture_compliance_violations",
        lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
    )
    assert arch_gate.main() == 1
