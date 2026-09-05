"""长稳与疲劳测试门禁（L5）.

锁定性能协议上限，并要求产品疲劳/长稳用例制品存在。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.checks.standards.artifacts import ArtifactKeys, artifact_hits
from tools.checks.standards.finding import finding
from tools.checks.standards.level import level_switch_hits
from tools.checks.standards.stage import run_standard_stage
from tools.support.gate_config import load_quality_gate as load_config

_LUMINA = Path(__file__).resolve().parents[3]
_SECTION = "endurance_standard"
_MIN_FATIGUE_ROUNDS = 100
_SWITCHES = (
    "require_perf_enable",
    "require_latency_cap",
    "require_protocol_warmup_timed",
    "require_endurance_tests",
    "require_min_fatigue_rounds",
)


def endurance_violations(config: dict[str, Any], *, root: Path | None = None) -> list[dict[str, str]]:
    """Collect L5 endurance / fatigue-test configuration violations."""
    standard = config.get(_SECTION, {})
    if not standard.get("enable", False):
        return []
    base = root or _LUMINA
    out = level_switch_hits(config, _SECTION, _SWITCHES, "L5长稳疲劳档要求该开关为 true")
    out.extend(_perf_enable_hits(config, standard))
    out.extend(_latency_cap_hits(config, standard))
    out.extend(_rounds_hits(standard))
    out.extend(_protocol_and_test_hits(base, standard))
    return out


def _perf_enable_hits(config: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_perf_enable", False)):
        return []
    if bool(config.get("perf_standard", {}).get("enable", False)):
        return []
    return [finding("perf_standard.enable", "L5长稳疲劳档要求 perf_standard.enable=true")]


def _latency_cap_hits(config: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_latency_cap", False)):
        return []
    limit = float(standard.get("max_latency_regression", 0.02))
    current = float(config.get("perf_standard", {}).get("max_latency_regression", limit + 1))
    if current <= limit:
        return []
    return [
        finding(
            "perf_standard.max_latency_regression",
            f"L5长稳疲劳档要求 max_latency_regression ≤ {limit}",
            int(current * 1000),
            int(limit * 1000),
        )
    ]


def _rounds_hits(standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_min_fatigue_rounds", False)):
        return []
    need = int(standard.get("min_fatigue_rounds", _MIN_FATIGUE_ROUNDS))
    if need >= _MIN_FATIGUE_ROUNDS:
        return []
    return [
        finding(
            "endurance_standard.min_fatigue_rounds",
            f"L5长稳疲劳档要求 min_fatigue_rounds ≥ {_MIN_FATIGUE_ROUNDS}",
            need,
            _MIN_FATIGUE_ROUNDS,
        )
    ]


def _protocol_and_test_hits(base: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    """Check timing protocol file and endurance test artifacts."""
    out = artifact_hits(
        base,
        {
            "require_protocol_warmup_timed": bool(standard.get("require_protocol_warmup_timed", False)),
            "protocol_files": [str(standard.get("protocol_file", "tools/checks/performance/protocol.py"))],
            "protocol_markers": list(standard.get("protocol_markers", ["warmup", "timed", "DEFAULT_TIMED"])),
        },
        ArtifactKeys(
            switch="require_protocol_warmup_timed",
            files_key="protocol_files",
            markers_key="protocol_markers",
            missing_issue="缺少 L4 计时协议文件（warmup+timed）",
            marker_issue="计时协议缺少 warmup/timed 线索",
        ),
    )
    out.extend(
        artifact_hits(
            base,
            standard,
            ArtifactKeys(
                switch="require_endurance_tests",
                files_key="endurance_test_files",
                markers_key="endurance_markers",
                missing_issue="缺少长稳/疲劳测试文件",
                marker_issue="长稳测试缺少疲劳线索（endurance/fatigue/rounds）",
            ),
        )
    )
    return out


def main() -> int:
    """CLI entry for endurance L5."""
    return run_standard_stage(
        section=_SECTION,
        stage="endurance-l5",
        load_config=load_config,
        collect=endurance_violations,
    )


if __name__ == "__main__":
    raise SystemExit(main())
