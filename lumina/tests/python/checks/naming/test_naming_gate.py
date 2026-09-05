"""Naming gate orchestration branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.naming import gate as naming_gate


def test_disabled_naming_returns_empty() -> None:
    """enable=false skips naming_violations."""
    assert naming_gate.naming_violations({"naming_standard": {"enable": False}}) == []


def test_scans_temp_c_root(tmp_path: Path) -> None:
    """Configured include_paths are scanned for C sources."""
    src = tmp_path / "algorithm"
    src.mkdir()
    (src / "util.c").write_text("int x(void){return 0;}\n", encoding="utf-8")
    config = {
        "naming_standard": {
            "enable": True,
            "level": "L0",
            "require_filename_rules": True,
            "require_symbol_rules": False,
            "require_macro_rules": False,
            "require_include_guard": False,
            "allow_baseline_macro_aliases": False,
            "include_paths": [str(src)],
            "file_patterns": [],
            "file_allowlist": [],
        }
    }
    hits = naming_gate.naming_violations(config)
    assert hits


def test_main_skip_pass_fail(monkeypatch: Any) -> None:
    """naming main covers skip / pass / fail exits."""
    monkeypatch.setattr(naming_gate, "load_config", lambda: {})
    assert naming_gate.main() == 0
    monkeypatch.setattr(
        naming_gate,
        "load_config",
        lambda: {"naming_standard": {"enable": False}},
    )
    assert naming_gate.main() == 0
    monkeypatch.setattr(
        naming_gate,
        "load_config",
        lambda: {"naming_standard": {"enable": True}},
    )
    monkeypatch.setattr(naming_gate, "naming_violations", lambda _c: [])
    assert naming_gate.main() == 0
    monkeypatch.setattr(
        naming_gate,
        "naming_violations",
        lambda _c: [{"target": "t", "issue": "x"}],
    )
    assert naming_gate.main() == 1
