"""Unit tests for document-quality L5 config and meta checks."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations

from tools.checks.docs.level import document_level_violations
from tools.checks.docs.meta import file_doc_violations
from tools.checks.docs.meta_parse import parse_meta_fields


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


def test_parse_meta_and_pass_sample(tmp_path: Path) -> None:
    """A minimal L5-shaped Markdown document produces no file hits."""
    source = tmp_path / "LUM-ARC-999_sample.md"
    source.write_text(
        "\n".join(
            [
                "# LUM-ARC-999 sample",
                "",
                "| 字段 | 内容 |",
                "|:---|:---|",
                "| 状态 | 草案 |",
                "| 版本 | 0.1 |",
                "| 日期 | 2026-09-05 |",
                "| 权威技能 | `lumina-arc-skill` |",
                "| 关联文档 | `LUM-ARC-001` |",
                "",
                "## 1. 范围",
                "",
                "body",
                "",
            ]
        ),
        encoding="utf-8",
    )
    domain = {
        "required_skill": "lumina-arc-skill",
        "doc_id_prefix": "LUM-ARC-",
    }
    standard = {
        "require_meta_table": True,
        "require_status_vocab": True,
        "require_skill_alignment": True,
        "require_h1_doc_id": True,
        "require_numbered_section": True,
        "status_vocab": ["生效", "草案", "计划"],
    }
    fields = parse_meta_fields(source.read_text(encoding="utf-8").splitlines())
    assert fields["状态"] == "草案"
    assert file_doc_violations(source, source.name, domain, standard) == []


def test_missing_skill_is_flagged(tmp_path: Path) -> None:
    """Authority skill cell must mention the domain skill."""
    source = tmp_path / "LUM-ENG-999.md"
    source.write_text(
        "\n".join(
            [
                "# LUM-ENG-999",
                "| 字段 | 内容 |",
                "| 状态 | 计划 |",
                "| 版本 | 0.1 |",
                "| 日期 | 2026-09-05 |",
                "| 权威技能 | other-skill |",
                "| 关联文档 | `LUM-ENG-001` |",
                "## 1. x",
            ]
        ),
        encoding="utf-8",
    )
    domain = {"required_skill": "lumina-eng-skill", "doc_id_prefix": "LUM-ENG-"}
    standard = {
        "require_meta_table": True,
        "require_status_vocab": True,
        "require_skill_alignment": True,
        "require_h1_doc_id": True,
        "require_numbered_section": True,
        "status_vocab": ["生效", "草案", "计划"],
    }
    hits = file_doc_violations(source, source.name, domain, standard)
    assert any("权威技能" in item["issue"] for item in hits)
