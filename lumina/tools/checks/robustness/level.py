"""L5 robustness-tier enforcement for ``[robustness_standard]``."""

from __future__ import annotations

from typing import Any

from tools.checks.robustness.finding import finding

_L5_SWITCHES = (
    "require_ha_check",
    "require_zero_unchecked_exceptions",
    "require_zero_none_risk",
    "require_global_state_cap",
    "require_boundary_tests",
)


def robustness_level_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Reject L5 robustness configs that disable any required switch."""
    standard = config.get("robustness_standard", {})
    if str(standard.get("level", "")).upper() != "L5":
        return []
    # 必须全开：L5 容错档禁止局部 false 降到存在性检查。
    return [
        finding(f"robustness_standard.{key}", "L5鲁棒性档要求该开关为 true")
        # 必须枚举五开关：漏一项即假绿。
        for key in _L5_SWITCHES
        if not bool(standard.get(key, False))
    ]
