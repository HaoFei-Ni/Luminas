"""HA gate: unchecked exceptions, mutable globals, None-reference risk."""

from __future__ import annotations

from typing import Any

from tools.arch_gate import project_files
from tools.ha_except import unchecked_exception_paths
from tools.ha_globals import max_global_state
from tools.ha_none import none_reference_risk


def ha_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Compare HA metrics against ``[thresholds]`` (fail closed)."""
    features = config.get("features", {})
    if not features.get("enable_ha_check", True):
        return []
    thresholds = config["thresholds"]
    files = project_files(config)
    out: list[dict[str, str]] = []
    unchecked, unchecked_loc = unchecked_exception_paths(files)
    globals_n, globals_loc = max_global_state(files)
    none_n, none_loc = none_reference_risk(files)
    _append(out, unchecked_loc or "ha", "未检异常路径超限", unchecked, thresholds["max_unchecked_exception_paths"])
    _append(out, globals_loc or "ha", "全局状态变量超限", globals_n, thresholds["max_global_state_variables"])
    _append(out, none_loc or "ha", "空引用风险超限", none_n, thresholds["max_none_reference_risk"])
    return out


def _append(out: list[dict[str, str]], target: str, issue: str, current: int, limit: int) -> None:
    """Append a violation when ``current`` exceeds ``limit``."""
    if current > limit:
        out.append({"target": target, "issue": issue, "current": str(current), "limit": str(limit)})
