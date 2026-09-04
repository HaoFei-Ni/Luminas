"""Unit tests for layout-quality L5 config and tree checks."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations

from tools.checks.layout.gate import layout_violations
from tools.checks.layout.level import layout_level_violations


def test_l5_rejects_disabled_product_switch() -> None:
    """L5 level must keep require_product_layers on."""
    config = {
        "layout_standard": {
            "level": "L5",
            "require_product_layers": False,
            "require_content_planes": True,
            "require_docs_domains": True,
            "require_ascii_dir_names": True,
            "forbid_banned_roots": True,
        }
    }
    hits = layout_level_violations(config)
    assert any("require_product_layers" in item["target"] for item in hits)


def test_missing_product_layer_flagged(tmp_path: Path) -> None:
    """Absent algorithm/ is a layout L5 failure."""
    (tmp_path / "kernel").mkdir()
    (tmp_path / "wrapper").mkdir()
    config = {
        "layout_standard": {
            "enable": True,
            "level": "L5",
            "require_product_layers": True,
            "require_content_planes": False,
            "require_docs_domains": False,
            "require_ascii_dir_names": False,
            "forbid_banned_roots": False,
            "product_layers": ["algorithm", "kernel", "wrapper"],
        }
    }
    hits = layout_violations(config, root=tmp_path)
    assert any(item["target"] == "algorithm" for item in hits)


def test_banned_common_root_flagged(tmp_path: Path) -> None:
    """Top-level common/ is forbidden under L5."""
    (tmp_path / "common").mkdir()
    config = {
        "layout_standard": {
            "enable": True,
            "level": "L0",
            "require_product_layers": False,
            "require_content_planes": False,
            "require_docs_domains": False,
            "require_ascii_dir_names": False,
            "forbid_banned_roots": True,
            "banned_roots": ["common"],
        }
    }
    hits = layout_violations(config, root=tmp_path)
    assert any(item["target"] == "common" for item in hits)
