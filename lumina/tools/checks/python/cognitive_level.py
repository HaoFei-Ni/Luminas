"""Cognitive-complexity tier caps for ``[thresholds].cognitive_complexity_level``.

L1 = Simple (≤5) · L2 = Moderate (≤10) · L3 = complexipy default (≤15) ·
L4 = High (≤20) · L5 = Very high (≤25). Cap table mirrors complexipy score bands.
"""

from __future__ import annotations

from typing import Any

# complexipy understanding-scores bands → named Luminas gate tiers.
_COGNITIVE_LEVEL_CAPS: dict[str, int] = {
    "L1": 5,
    "L2": 10,
    "L3": 15,
    "L4": 20,
    "L5": 25,
}


def cognitive_level_cap(level: str) -> int | None:
    """Return max allowed cognitive complexity for ``level``, or None if unknown."""
    return _COGNITIVE_LEVEL_CAPS.get(str(level).upper())


def cognitive_level_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Reject configs whose ``max_cognitive_complexity`` exceeds the named tier cap."""
    thresholds = config.get("thresholds", {})
    level = str(thresholds.get("cognitive_complexity_level", "")).upper()
    if not level:
        return []
    cap = cognitive_level_cap(level)
    if cap is None:
        return [
            {
                "target": "thresholds.cognitive_complexity_level",
                "issue": f"未知认知复杂度档位 {level}（允许 L1–L5）",
                "current": level,
                "limit": "L1|L2|L3|L4|L5",
            }
        ]
    current = int(thresholds.get("max_cognitive_complexity", cap))
    if current <= cap:
        return []
    return [
        {
            "target": "thresholds.max_cognitive_complexity",
            "issue": f"认知复杂度档位 {level} 要求阈值 ≤ {cap}",
            "current": str(current),
            "limit": str(cap),
        }
    ]
