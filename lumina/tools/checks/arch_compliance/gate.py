"""架构合规性测试门禁（L5）.

锁定 ``enable_architecture_check`` 与环/扇出/继承/克隆阈值，并要求架构单测制品。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.checks.standards.artifacts import ArtifactKeys, artifact_hits
from tools.checks.standards.caps import feature_flag_hits, threshold_cap_hits
from tools.checks.standards.level import level_switch_hits
from tools.checks.standards.stage import run_standard_stage
from tools.support.gate_config import load_quality_gate as load_config

_LUMINA = Path(__file__).resolve().parents[3]
_SECTION = "architecture_standard"
_SWITCHES = (
    "require_architecture_check",
    "require_zero_cycles",
    "require_fan_out_cap",
    "require_inheritance_cap",
    "require_clone_cap",
    "require_architecture_tests",
)
_CAPS = (
    ("require_zero_cycles", "max_cyclic_dependencies"),
    ("require_fan_out_cap", "max_module_fan_out"),
    ("require_inheritance_cap", "max_inheritance_depth"),
    ("require_clone_cap", "max_duplicate_code_blocks"),
)


def architecture_compliance_violations(
    config: dict[str, Any],
    *,
    root: Path | None = None,
) -> list[dict[str, str]]:
    """Collect L5 architecture-compliance configuration violations."""
    standard = config.get(_SECTION, {})
    if not standard.get("enable", False):
        return []
    base = root or _LUMINA
    out = level_switch_hits(config, _SECTION, _SWITCHES, "L5架构合规档要求该开关为 true")
    out.extend(
        feature_flag_hits(
            config,
            standard,
            switch="require_architecture_check",
            feature_key="enable_architecture_check",
            issue="L5架构合规档要求 enable_architecture_check=true",
        )
    )
    out.extend(threshold_cap_hits(config, standard, list(_CAPS), issue_prefix="L5架构合规档"))
    out.extend(
        artifact_hits(
            base,
            standard,
            ArtifactKeys(
                switch="require_architecture_tests",
                files_key="architecture_test_files",
                markers_key="architecture_test_markers",
                missing_issue="缺少架构合规性测试文件",
                marker_issue="架构测试缺少合规线索（环/扇出/继承/克隆）",
            ),
        )
    )
    return out


def main() -> int:
    """CLI entry for architecture-compliance L5."""
    return run_standard_stage(
        section=_SECTION,
        stage="arch-compliance-l5",
        load_config=load_config,
        collect=architecture_compliance_violations,
    )


if __name__ == "__main__":
    raise SystemExit(main())
