"""Document L5 level-config branch coverage."""

from __future__ import annotations

from tools.checks.docs.level import document_level_violations


def test_non_l5_skips_level_enforcement() -> None:
    """Non-L5 configs do not emit switch violations."""
    config = {"document_standard": {"level": "L0", "require_meta_table": False}}
    assert document_level_violations(config) == []


def test_domain_l5_locks_global_switches() -> None:
    """Any domain at L5 forces global L5 switch enforcement."""
    config = {
        "document_standard": {
            "level": "L0",
            "architecture": {"level": "L5"},
            "require_meta_table": False,
            "require_status_vocab": True,
            "require_skill_alignment": True,
            "require_h1_doc_id": True,
            "require_numbered_section": True,
        }
    }
    hits = document_level_violations(config)
    assert any("require_meta_table" in item["target"] for item in hits)


def test_l5_rejects_disabled_meta_switch() -> None:
    """L5 level must keep require_meta_table on."""
    config = {
        "document_standard": {
            "level": "L5",
            "require_meta_table": False,
            "require_status_vocab": True,
            "require_skill_alignment": True,
            "require_h1_doc_id": True,
            "require_numbered_section": True,
        }
    }
    hits = document_level_violations(config)
    assert any("require_meta_table" in item["target"] for item in hits)


def test_l5_passes_when_all_switches_on() -> None:
    """Complete L5 switch set yields no level violations."""
    config = {
        "document_standard": {
            "level": "L5",
            "require_meta_table": True,
            "require_status_vocab": True,
            "require_skill_alignment": True,
            "require_h1_doc_id": True,
            "require_numbered_section": True,
        }
    }
    assert document_level_violations(config) == []
