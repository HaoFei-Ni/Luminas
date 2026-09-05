"""Document gate orchestration and CLI branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.docs import gate as docs_gate


def test_disabled_standard_returns_empty() -> None:
    """enable=false short-circuits document_violations."""
    assert docs_gate.document_violations({"document_standard": {"enable": False}}) == []


def test_missing_include_root_flagged(tmp_path: Path) -> None:
    """Non-existent include_paths emit a directory finding."""
    config: dict[str, Any] = {
        "document_standard": {
            "enable": True,
            "level": "L0",
            "architecture": {
                "include_paths": [str(tmp_path / "missing")],
                "file_glob": "LUM-*.md",
                "required_skill": "lumina-arc-skill",
                "doc_id_prefix": "LUM-ARC-",
            },
        }
    }
    hits = docs_gate.document_violations(config)
    assert any("目录不存在" in item["issue"] for item in hits)


def test_scans_existing_markdown(tmp_path: Path) -> None:
    """Existing domain root with a matching file is scanned."""
    root = tmp_path / "arc"
    root.mkdir()
    (root / "LUM-ARC-1.md").write_text("# LUM-ARC-1\n## 1. x\n", encoding="utf-8")
    config: dict[str, Any] = {
        "document_standard": {
            "enable": True,
            "level": "L0",
            "require_meta_table": True,
            "architecture": {
                "include_paths": [str(root)],
                "file_glob": "LUM-ARC-*.md",
                "required_skill": "lumina-arc-skill",
                "doc_id_prefix": "LUM-ARC-",
            },
        }
    }
    hits = docs_gate.document_violations(config)
    assert any("缺字段" in item["issue"] for item in hits)


def test_non_dict_domain_skipped() -> None:
    """Non-dict domain entries are ignored without error."""
    config = {
        "document_standard": {
            "enable": True,
            "level": "L0",
            "architecture": "skip-me",
        }
    }
    assert docs_gate.document_violations(config) == []


def test_main_skip_pass_and_fail(monkeypatch: Any) -> None:
    """main covers disable / pass / fail exit paths."""
    monkeypatch.setattr(docs_gate, "load_config", lambda: {"document_standard": {"enable": False}})
    assert docs_gate.main() == 0
    monkeypatch.setattr(
        docs_gate,
        "load_config",
        lambda: {"document_standard": {"enable": True, "level": "L0"}},
    )
    monkeypatch.setattr(docs_gate, "document_violations", lambda _c: [])
    assert docs_gate.main() == 0
    monkeypatch.setattr(
        docs_gate,
        "document_violations",
        lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
    )
    assert docs_gate.main() == 1
