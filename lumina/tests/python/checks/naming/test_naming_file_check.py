"""Naming file_check / macro_check branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations

from tools.checks.naming.file_check import check_one_file
from tools.checks.naming.macro_check import macro_issue

_ALL_ON = {
    "require_filename_rules": True,
    "require_symbol_rules": True,
    "require_macro_rules": True,
    "require_include_guard": True,
}
_ALL_OFF = {key: False for key in _ALL_ON}


def test_macro_issue_branches() -> None:
    """Baseline alias / LUMA ok / plain reject paths."""
    assert macro_issue("LUMA_BASELINE_X", False) is not None
    assert macro_issue("LUMA_BASELINE_X", True) is None
    assert macro_issue("LUMA_OK", False) is None
    assert macro_issue("_private", False) is None
    assert macro_issue("FOO_H", False) is None
    assert macro_issue("PLAIN", False) is not None


def test_cpp_skips_symbol_macro(tmp_path: Path) -> None:
    """C++ files only run filename rules then return."""
    path = tmp_path / "luma_bind_native.cpp"
    path.write_text("// bind\n", encoding="utf-8")
    hits = check_one_file(path, frozenset(), False, _ALL_ON)
    assert hits == []


def test_bad_c_filename_and_symbol(tmp_path: Path) -> None:
    """Vague filename and non-luma symbol are flagged."""
    path = tmp_path / "util.c"
    path.write_text("int bad(void) {\n  return 0;\n}\n", encoding="utf-8")
    hits = check_one_file(path, frozenset(), False, _ALL_ON)
    assert any("前缀" in item["issue"] or "模糊" in item["issue"] for item in hits)


def test_switches_off_and_clean_header(tmp_path: Path) -> None:
    """All switches off yields []; clean header passes filename."""
    path = tmp_path / "luma_kv.h"
    path.write_text(
        "#ifndef LUMA_KV_H\n#define LUMA_KV_H\n#define LUMA_OK 0\n#endif\n",
        encoding="utf-8",
    )
    assert check_one_file(path, frozenset(), False, _ALL_OFF) == []
    hits = check_one_file(path, frozenset(), False, _ALL_ON)
    assert not any("宏须" in item["issue"] for item in hits)


def test_bad_macro_and_guard(tmp_path: Path) -> None:
    """Non-LUMA define and missing guard are flagged."""
    path = tmp_path / "luma_kv_codec.c"
    path.write_text("#define PLAIN 1\nint luma_kv_encode_f32(void){return 0;}\n", encoding="utf-8")
    hits = check_one_file(path, frozenset(), False, _ALL_ON)
    assert any("宏须" in item["issue"] for item in hits)
