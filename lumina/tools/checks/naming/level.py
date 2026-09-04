"""L5 file-naming tier enforcement for ``[naming_standard]``."""

from __future__ import annotations

from typing import Any

_L5_SWITCHES = (
    "require_filename_rules",
    "require_symbol_rules",
    "require_macro_rules",
    "require_include_guard",
)


def naming_level_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Reject L5 naming configs that disable rules or allow baseline macros."""
    standard = config.get("naming_standard", {})
    if str(standard.get("level", "")).upper() != "L5":
        return []
    out = [
        _hit(f"naming_standard.{key}", "L5文件命名档要求该开关为 true")
        # 必须枚举四开关：漏一项即假绿。
        for key in _L5_SWITCHES
        if not bool(standard.get(key, False))
    ]
    if bool(standard.get("allow_baseline_macro_aliases", True)):
        out.append(
            _hit(
                "naming_standard.allow_baseline_macro_aliases",
                "L5文件命名档禁止 allow_baseline_macro_aliases=true",
            )
        )
    return out


def _hit(target: str, issue: str) -> dict[str, str]:
    return {"target": target, "issue": issue, "current": "0", "limit": "1"}
