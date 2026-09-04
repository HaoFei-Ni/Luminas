"""Unit tests for L5 comment-tier config enforcement."""

from __future__ import annotations

from tools.checks.comments.level import comment_level_violations, numeric_contract_banner_violations


def test_l5_rejects_disabled_why_switch() -> None:
    """L5 level must keep require_why_semantics on."""
    config = {
        "comment_standard": {
            "level": "L5",
            "require_file_banner": True,
            "require_function_doc": True,
            "require_header_decl_doc": True,
            "require_inline_on_complex": True,
            "require_why_semantics": False,
        }
    }
    hits = comment_level_violations(config)
    assert any("require_why_semantics" in item["target"] for item in hits)


def test_l5_passes_when_all_switches_on() -> None:
    """Complete L5 switch set yields no level violations."""
    config = {
        "comment_standard": {
            "level": "L5",
            "require_file_banner": True,
            "require_function_doc": True,
            "require_header_decl_doc": True,
            "require_inline_on_complex": True,
            "require_why_semantics": True,
        }
    }
    assert comment_level_violations(config) == []


def test_numeric_contract_banner_requires_marker(tmp_path) -> None:  # noqa: ANN001
    """Core path without L5/ulp clue in banner is flagged."""
    source = tmp_path / "luma_kv_encode.c"
    source.write_text("/* codec only */\nint f(void){return 0;}\n", encoding="utf-8")
    item = type("Item", (), {"file_key": "algorithm/luma_kv_encode.c", "path": str(source)})()
    config = {
        "comment_standard": {
            "require_numeric_contract_banner": True,
            "numeric_contract_file_patterns": ["algorithm/luma_kv_*.c"],
            "numeric_contract_markers": ["L5", "2-ulp", "bit-exact"],
        }
    }
    assert len(numeric_contract_banner_violations([item], config)) == 1
    source.write_text("/* 工程 L5 / bit-exact */\nint f(void){return 0;}\n", encoding="utf-8")
    assert numeric_contract_banner_violations([item], config) == []
