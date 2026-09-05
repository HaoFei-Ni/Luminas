"""L5 switch-lock helpers for named ``*_standard`` sections."""

from __future__ import annotations

from typing import Any

from tools.checks.standards.finding import finding


def level_switch_hits(
    config: dict[str, Any],
    section: str,
    switches: tuple[str, ...],
    issue: str,
) -> list[dict[str, str]]:
    """Reject L5 configs that disable any required switch in ``section``."""
    standard = config.get(section, {})
    if str(standard.get("level", "")).upper() != "L5":
        return []
    # 必须全开：L5 档禁止局部 false 降到存在性检查。
    return [
        finding(f"{section}.{key}", issue)
        # 必须枚举配置开关：漏一项即假绿。
        for key in switches
        if not bool(standard.get(key, False))
    ]
