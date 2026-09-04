"""Macro naming checks for the naming gate."""

from __future__ import annotations


def macro_issue(name: str, allow_aliases: bool) -> str | None:
    """Return a violation message for one macro name, or None if OK."""
    if _is_forbidden_baseline_alias(name, allow_aliases):
        return "禁止 LUMA_BASELINE_* 兼容别名"
    if _macro_name_ok(name):
        return None
    return f"宏须 LUMA_ 前缀: {name}"


def _is_forbidden_baseline_alias(name: str, allow_aliases: bool) -> bool:
    return name.startswith("LUMA_") and not allow_aliases and "BASELINE" in name


def _macro_name_ok(name: str) -> bool:
    return name.startswith("LUMA_") or name.endswith(("_H", "_HPP")) or name.startswith("_")
