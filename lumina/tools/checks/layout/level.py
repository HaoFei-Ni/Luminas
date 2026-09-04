"""L5 layout-tier enforcement for ``[layout_standard]``."""

from __future__ import annotations

from typing import Any

from tools.checks.layout.finding import finding

_L5_SWITCHES = (
    "require_product_layers",
    "require_content_planes",
    "require_docs_domains",
    "require_ascii_dir_names",
    "forbid_banned_roots",
)


def layout_level_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Reject L5 layout configs that disable any required switch."""
    standard = config.get("layout_standard", {})
    if str(standard.get("level", "")).upper() != "L5":
        return []
    # 必须全开：L5 目录档禁止局部 false 降到存在性检查。
    return [
        finding(f"layout_standard.{key}", "L5目录结构档要求该开关为 true")
        # 必须枚举五开关：漏一项即假绿。
        for key in _L5_SWITCHES
        if not bool(standard.get(key, False))
    ]
