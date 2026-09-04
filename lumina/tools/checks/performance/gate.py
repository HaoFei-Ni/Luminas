"""L4 性能门禁（最高档）：协议计时 + 相对校准基线回归.

相对分数 ``kernel_mean / calib_mean``，跨机绝对时间漂移不影响裁决；
相对分数相对仓库基线升高超过 2% 则失败。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.checks.performance.gate_compare import compare_scores, missing_required_violations, violation
from tools.checks.performance.protocol import (
    DEFAULT_MAX_REGRESSION,
    interleaved_relative_score,
)
from tools.checks.performance.workloads import bench_workloads, make_calib
from tools.support.gate_config import load_quality_gate as load_config

_BASELINE_SCHEMA = 1


def perf_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Run L4 benches and compare relative scores to the committed baseline."""
    standard = config.get("perf_standard", {})
    if not standard.get("enable", False):
        return []
    ratio_issue = _ratio_cap_violation(standard)
    if ratio_issue:
        return ratio_issue
    scores = _measure_relative_scores()
    missing = missing_required_violations(scores, standard)
    if missing:
        return missing
    baseline_path = Path(standard.get("baseline_path", "tests/python/baselines/l4_perf_baseline.json"))
    baseline_issue = _load_baseline_or_violation(baseline_path)
    if isinstance(baseline_issue, list):
        return baseline_issue
    max_ratio = float(standard.get("max_latency_regression", DEFAULT_MAX_REGRESSION))
    return compare_scores(scores, baseline_issue.get("scores", {}), max_ratio)


def _ratio_cap_violation(standard: dict[str, Any]) -> list[dict[str, str]]:
    """Reject configs that loosen the 2% industrial latency cap."""
    max_ratio = float(standard.get("max_latency_regression", DEFAULT_MAX_REGRESSION))
    if max_ratio <= DEFAULT_MAX_REGRESSION:
        return []
    return [
        violation(
            "perf_standard",
            f"最高档 max_latency_regression 不得超过 {DEFAULT_MAX_REGRESSION}",
            max_ratio,
            DEFAULT_MAX_REGRESSION,
        )
    ]


def _load_baseline_or_violation(baseline_path: Path) -> dict[str, Any] | list[dict[str, str]]:
    """Load baseline JSON or return a single violation list."""
    if not baseline_path.exists():
        return [violation(str(baseline_path), "缺少 L4 性能基线文件（最高档强制）", 0, 1)]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if int(baseline.get("schema", 0)) == _BASELINE_SCHEMA:
        return baseline
    return [
        violation(
            str(baseline_path),
            "性能基线 schema 不匹配",
            int(baseline.get("schema", 0)),
            _BASELINE_SCHEMA,
        )
    ]


def _measure_relative_scores() -> dict[str, float]:
    """Return kernel/calib ratios via interleaved wall time (stable on Windows)."""
    scores: dict[str, float] = {}
    calib_fn = make_calib()
    # 必须逐 workload 计分：禁止把校准自身再当 bench。
    for name, workload in bench_workloads().items():
        scores[name] = interleaved_relative_score(calib_fn, workload)
    return scores


def main() -> int:
    """Run L4 perf gate and print a compact summary."""
    config = load_config()
    if not config.get("perf_standard", {}).get("enable", False):
        print("[INFO] perf_standard 未启用，跳过性能门禁")
        return 0
    try:
        violations = perf_violations(config)
    except Exception as exc:  # noqa: BLE001 — 门禁入口需把协议错误打成失败
        print(f"[FAIL] perf-l4: {exc}")
        return 1
    print(f"[INFO] perf-l4 findings={len(violations)}")
    # 必须单遍输出：便于 CI 逐条定位失败项。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print("[FAIL] perf-l4")
        return 1
    print("[PASS] perf-l4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
