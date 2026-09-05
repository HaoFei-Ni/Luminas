"""Threshold and HA-feature locks for robustness L5."""

from __future__ import annotations

from typing import Any

from tools.checks.robustness.finding import finding


def feature_ha_hits(config: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, str]]:
    """Require ``features.enable_ha_check`` when the L5 switch is on."""
    if not bool(standard.get("require_ha_check", False)):
        return []
    if bool(config.get("features", {}).get("enable_ha_check", False)):
        return []
    return [finding("features.enable_ha_check", "L5鲁棒性档要求 enable_ha_check=true")]


def threshold_cap_hits(config: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, str]]:
    """Reject thresholds looser than the L5 robustness caps."""
    thresholds = config.get("thresholds", {})
    out: list[dict[str, str]] = []
    out.extend(_cap_hit(thresholds, standard, "require_zero_unchecked_exceptions", "max_unchecked_exception_paths"))
    out.extend(_cap_hit(thresholds, standard, "require_zero_none_risk", "max_none_reference_risk"))
    out.extend(_cap_hit(thresholds, standard, "require_global_state_cap", "max_global_state_variables"))
    return out


def _cap_hit(
    thresholds: dict[str, Any],
    standard: dict[str, Any],
    switch: str,
    key: str,
) -> list[dict[str, str]]:
    """Emit one finding when a threshold exceeds the configured L5 cap."""
    if not bool(standard.get(switch, False)):
        return []
    limit = int(standard.get(key, 0))
    current = int(thresholds.get(key, limit + 1))
    if current <= limit:
        return []
    return [finding(f"thresholds.{key}", f"L5鲁棒性档要求 {key} ≤ {limit}", current, limit)]
