"""Layout tree / plane / ascii branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.layout import gate as layout_gate
from tools.checks.layout.level import layout_level_violations
from tools.checks.layout.tree import ascii_dir_hits


def test_l5_passes_when_complete() -> None:
    """All L5 layout switches on yields no level hits."""
    config = {
        "layout_standard": {
            "level": "L5",
            "require_product_layers": True,
            "require_content_planes": True,
            "require_docs_domains": True,
            "require_ascii_dir_names": True,
            "forbid_banned_roots": True,
        }
    }
    assert layout_level_violations(config) == []


def test_non_l5_skips_level() -> None:
    """Non-L5 layout configs skip switch enforcement."""
    assert layout_level_violations({"layout_standard": {"level": "L0"}}) == []


def test_planes_docs_and_ascii(tmp_path: Path) -> None:
    """Missing planes/docs and bad ASCII names are flagged."""
    (tmp_path / "BadDir").mkdir()
    config = {
        "layout_standard": {
            "enable": True,
            "level": "L0",
            "require_product_layers": False,
            "require_content_planes": True,
            "require_docs_domains": True,
            "require_ascii_dir_names": True,
            "forbid_banned_roots": False,
            "content_planes": ["tools"],
            "docs_domains": ["docs/arc"],
            "ascii_scan_roots": ["."],
            "ascii_ignore_dir_names": [],
        }
    }
    # scan root "." relative to tmp_path: place BadDir under a named scan root
    scan = tmp_path / "scan"
    scan.mkdir()
    (scan / "CamelCase").mkdir()
    config["layout_standard"]["ascii_scan_roots"] = ["scan"]
    hits = layout_gate.layout_violations(config, root=tmp_path)
    assert any(item["target"] == "tools" for item in hits)
    assert any("docs/arc" in item["target"] for item in hits)
    assert any("CamelCase" in item["issue"] for item in hits)


def test_ascii_ignores_and_missing_scan_root(tmp_path: Path) -> None:
    """Ignored names pass; missing scan roots contribute nothing."""
    root = tmp_path / "algorithm"
    root.mkdir()
    (root / "__pycache__").mkdir()
    hits = ascii_dir_hits(tmp_path, ["algorithm", "missing"], frozenset({"__pycache__"}))
    assert hits == []


def test_disabled_and_default_lists(tmp_path: Path) -> None:
    """Disabled helpers return []; defaults apply when lists omitted."""
    config = {
        "layout_standard": {
            "enable": True,
            "level": "L0",
            "require_product_layers": True,
            "require_content_planes": False,
            "require_docs_domains": False,
            "require_ascii_dir_names": False,
            "forbid_banned_roots": False,
        }
    }
    hits = layout_gate.layout_violations(config, root=tmp_path)
    assert any(item["target"] == "algorithm" for item in hits)


def test_main_paths(monkeypatch: Any) -> None:
    """layout main covers skip / pass / fail."""
    monkeypatch.setattr(layout_gate, "load_config", lambda: {"layout_standard": {"enable": False}})
    assert layout_gate.main() == 0
    monkeypatch.setattr(layout_gate, "load_config", lambda: {"layout_standard": {"enable": True}})
    monkeypatch.setattr(layout_gate, "layout_violations", lambda _c: [])
    assert layout_gate.main() == 0
    monkeypatch.setattr(
        layout_gate,
        "layout_violations",
        lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
    )
    assert layout_gate.main() == 1
