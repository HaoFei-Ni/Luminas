"""Document meta / H1 / section branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations

from tools.checks.docs.meta import file_doc_violations
from tools.checks.docs.meta_parse import parse_meta_fields

_DOMAIN = {"required_skill": "lumina-arc-skill", "doc_id_prefix": "LUM-ARC-"}
_OFF = {
    "require_meta_table": False,
    "require_status_vocab": False,
    "require_skill_alignment": False,
    "require_h1_doc_id": False,
    "require_numbered_section": False,
}


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_parse_skips_colon_keys_and_noise() -> None:
    """Colon keys and non-table lines are ignored; ## stops parsing."""
    lines = [
        "# LUM-ARC-1",
        "noise",
        "| :align | x |",
        "| 状态 | 计划 |",
        "## 1. stop",
        "| 版本 | 丢弃 |",
    ]
    assert parse_meta_fields(lines) == {"状态": "计划"}


def test_missing_meta_and_bad_status(tmp_path: Path) -> None:
    """Missing fields and illegal status each emit findings."""
    path = _write(
        tmp_path / "LUM-ARC-1.md",
        "# Title\n| 状态 | 草稿 |\n| 版本 | 0.1 |\n",
    )
    standard = {**_OFF, "require_meta_table": True, "require_status_vocab": True}
    hits = file_doc_violations(path, path.name, _DOMAIN, standard)
    assert any("缺字段" in item["issue"] for item in hits)
    assert any("状态用语" in item["issue"] for item in hits)


def test_h1_and_section_failures(tmp_path: Path) -> None:
    """Missing doc-id prefix and numbered section are flagged."""
    path = _write(tmp_path / "x.md", "plain\n| 状态 | 计划 |\n")
    standard = {**_OFF, "require_h1_doc_id": True, "require_numbered_section": True}
    hits = file_doc_violations(path, path.name, _DOMAIN, standard)
    assert any("H1" in item["issue"] for item in hits)
    assert any("编号章节" in item["issue"] for item in hits)


def test_switches_off_skip_checks(tmp_path: Path) -> None:
    """Disabled switches produce no file-level findings."""
    path = _write(tmp_path / "x.md", "no meta\n")
    assert file_doc_violations(path, path.name, _DOMAIN, _OFF) == []


def test_skill_pass_and_empty_required(tmp_path: Path) -> None:
    """Matching skill passes; empty required_skill still demands a cell hit path."""
    path = _write(
        tmp_path / "LUM-ARC-1.md",
        "# LUM-ARC-1\n| 权威技能 | `lumina-arc-skill` |\n## 1. x\n",
    )
    on = {**_OFF, "require_skill_alignment": True}
    assert file_doc_violations(path, path.name, _DOMAIN, on) == []
    empty = {"required_skill": "", "doc_id_prefix": "LUM-ARC-"}
    hits = file_doc_violations(path, path.name, empty, on)
    assert any("权威技能" in item["issue"] for item in hits)


def test_status_suffix_and_complete_meta_pass(tmp_path: Path) -> None:
    """生效（…） suffix and full meta table pass L5 file checks."""
    path = _write(
        tmp_path / "LUM-ARC-1.md",
        "\n".join(
            [
                "# LUM-ARC-1 title",
                "| 字段 | 内容 |",
                "| 状态 | 生效（最小） |",
                "| 版本 | 0.1 |",
                "| 日期 | 2026-09-05 |",
                "| 权威技能 | `lumina-arc-skill` |",
                "| 关联文档 | `LUM-ARC-001` |",
                "## 1. 范围",
            ]
        ),
    )
    standard = {
        "require_meta_table": True,
        "require_status_vocab": True,
        "require_skill_alignment": True,
        "require_h1_doc_id": True,
        "require_numbered_section": True,
        "status_vocab": ["生效", "草案", "计划"],
    }
    assert file_doc_violations(path, path.name, _DOMAIN, standard) == []
