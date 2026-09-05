"""端到端集成测试门禁（L5）.

要求产品 bind+kernel L3 集成用例与 C 产品路径集成线索存在。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.checks.standards.artifacts import ArtifactKeys, artifact_hits
from tools.checks.standards.level import level_switch_hits
from tools.checks.standards.stage import run_standard_stage
from tools.support.gate_config import load_quality_gate as load_config

_LUMINA = Path(__file__).resolve().parents[3]
_SECTION = "integration_standard"
_SWITCHES = (
    "require_python_l3_tests",
    "require_c_product_tests",
    "require_native_marker",
    "require_roundtrip_marker",
    "require_bind_kernel_agreement",
)


def integration_violations(config: dict[str, Any], *, root: Path | None = None) -> list[dict[str, str]]:
    """Collect L5 end-to-end integration-test configuration violations."""
    standard = config.get(_SECTION, {})
    if not standard.get("enable", False):
        return []
    base = root or _LUMINA
    out = level_switch_hits(config, _SECTION, _SWITCHES, "L5端到端集成档要求该开关为 true")
    out.extend(
        artifact_hits(
            base,
            standard,
            ArtifactKeys(
                switch="require_python_l3_tests",
                files_key="python_integration_files",
                markers_key="python_integration_markers",
                missing_issue="缺少 Python L3 集成测试文件",
                marker_issue="Python 集成测试缺少 L3/native/roundtrip 线索",
            ),
        )
    )
    out.extend(
        artifact_hits(
            base,
            standard,
            ArtifactKeys(
                switch="require_c_product_tests",
                files_key="c_integration_files",
                markers_key="c_integration_markers",
                missing_issue="缺少 C 产品路径集成测试文件",
                marker_issue="C 集成测试缺少 L1/L5/roundtrip 线索",
            ),
        )
    )
    return out


def main() -> int:
    """CLI entry for integration L5."""
    return run_standard_stage(
        section=_SECTION,
        stage="integration-l5",
        load_config=load_config,
        collect=integration_violations,
    )


if __name__ == "__main__":
    raise SystemExit(main())
