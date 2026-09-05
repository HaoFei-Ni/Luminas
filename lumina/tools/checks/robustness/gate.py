"""鲁棒性与异常容错测试门禁（L5）.

真值源：``quality-gate.toml`` ``[robustness_standard]``。
锁定 HA 开关与阈值，并要求产品/C 边界（L2 丑输入）测试存在。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.checks.robustness.boundary import boundary_test_hits
from tools.checks.robustness.caps import feature_ha_hits, threshold_cap_hits
from tools.checks.robustness.level import robustness_level_violations
from tools.support.gate_config import load_quality_gate as load_config

_LUMINA = Path(__file__).resolve().parents[3]


def robustness_violations(config: dict[str, Any], *, root: Path | None = None) -> list[dict[str, str]]:
    """Collect L5 robustness / fault-tolerance configuration violations."""
    standard = config.get("robustness_standard", {})
    if not standard.get("enable", False):
        return []
    base = root or _LUMINA
    out = robustness_level_violations(config)
    out.extend(feature_ha_hits(config, standard))
    out.extend(threshold_cap_hits(config, standard))
    out.extend(boundary_test_hits(base, standard))
    return out


def main() -> int:
    """CLI entry for the robustness-quality stage."""
    config = load_config()
    standard = config.get("robustness_standard", {})
    if not standard.get("enable", False):
        print("[INFO] robustness_standard 未启用，跳过鲁棒性门禁")
        return 0
    violations = robustness_violations(config)
    print(f"[INFO] robustness-l5 findings={len(violations)}")
    # 单遍：逐条输出，避免汇总丢失定位。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print("[FAIL] robustness-l5")
        return 1
    print("[PASS] robustness-l5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
