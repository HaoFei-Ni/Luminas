"""Feature-flag and threshold-cap locks for L5 standard gates."""

from __future__ import annotations

from typing import Any

from tools.checks.standards.finding import finding


def feature_flag_hits(
    config: dict[str, Any],
    standard: dict[str, Any],
    *,
    switch: str,
    feature_key: str,
    issue: str,
) -> list[dict[str, str]]:
    """Require ``features.<feature_key>`` when ``standard[switch]`` is on."""
    if not bool(standard.get(switch, False)):
        return []
    if bool(config.get("features", {}).get(feature_key, False)):
        return []
    return [finding(f"features.{feature_key}", issue)]


def threshold_cap_hits(
    config: dict[str, Any],
    standard: dict[str, Any],
    specs: list[tuple[str, str]],
    *,
    issue_prefix: str,
) -> list[dict[str, str]]:
    """Reject thresholds looser than caps named in ``standard``.

    Each spec is ``(switch_name, threshold_key)``; the cap value is ``standard[threshold_key]``.
    """
    thresholds = config.get("thresholds", {})
    out: list[dict[str, str]] = []
    # 单遍规格：每个阈值独立裁决，避免漏锁一项。
    for switch, key in specs:
        out.extend(_one_cap(thresholds, standard, switch, key, issue_prefix))
    return out


def _one_cap(
    thresholds: dict[str, Any],
    standard: dict[str, Any],
    switch: str,
    key: str,
    issue_prefix: str,
) -> list[dict[str, str]]:
    """Emit one finding when a threshold exceeds its L5 cap."""
    if not bool(standard.get(switch, False)):
        return []
    limit = int(standard.get(key, 0))
    current = int(thresholds.get(key, limit + 1))
    if current <= limit:
        return []
    return [finding(f"thresholds.{key}", f"{issue_prefix}要求 {key} ≤ {limit}", current, limit)]
