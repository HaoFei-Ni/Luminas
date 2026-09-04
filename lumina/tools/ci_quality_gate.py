#!/usr/bin/env python3
"""Full quality gate: four checks plus a health-overview Markdown report.

本执行器为「全量四项质量门禁」的 CI/本地手动入口（提交前的秒级认知复杂度
强校验见 complexity_precommit.py）。职责：

1. 读取 quality-gate.toml（阈值/开关/排除/报告文案）。
2. 复杂度取自 complexipy JSON（多版本 schema 由 quality_metrics 归一化）；
   行数指标用 Python AST 原生测量，与 complexipy 版本彻底解耦。
3. 执行四项校验：单文件物理行数、单文件函数数量、单函数物理行数、认知复杂度。
4. 生成对齐行业结构的 Markdown 报告：代码健康度概览 + 违规汇总 + 全量明细。

依赖扫描链（工作目录须为 lumina/）：
    uv run complexipy && uv run python -m tools.ci_quality_gate
"""

from __future__ import annotations

import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from tools import quality_metrics
from tools.quality_metrics import FileMetrics, FunctionMetrics


def load_config(config_path: str = "quality-gate.toml") -> Dict[str, Any]:
    """Load and parse the quality-gate TOML configuration file.

    Args:
        config_path: config file path relative to the lumina/ cwd.

    Returns:
        Parsed configuration dictionary.

    Raises:
        SystemExit: when the config file does not exist.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with config_file.open("rb") as handle:
        return dict(tomllib.load(handle))


def build_violation(target: str, issue: str, current: int, limit: int) -> Dict[str, str]:
    """Build a single normalized violation record for reporting.

    Args:
        target: violating file or function locator.
        issue: violation description.
        current: observed value.
        limit: configured threshold.

    Returns:
        Standardized violation record dictionary.
    """
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


def validate_quality(
    file_metrics: List[FileMetrics],
    function_metrics: List[FunctionMetrics],
    config: Dict[str, Any],
) -> Tuple[bool, List[Dict[str, str]]]:
    """Run every enabled quality check over the measured metrics.

    Args:
        file_metrics: per-file metrics from the AST measurement.
        function_metrics: per-function metrics with attached complexity.
        config: full quality-gate configuration.

    Returns:
        (whether every check passed, violation records).
    """
    violations = _file_level_violations(file_metrics, config)
    violations.extend(_function_level_violations(function_metrics, config))
    return not violations, violations


def _over_limit(enabled: bool, value: int | None, limit: int) -> bool:
    """Return True when a check is enabled and a measured value exceeds its limit.

    ``value`` may be ``None`` for optional metrics (e.g. missing complexity).
    """
    return enabled and value is not None and value > limit


def _file_level_violations(file_metrics: List[FileMetrics], config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Check per-file physical lines and per-file function counts."""
    thresholds = config["thresholds"]
    features = config["features"]
    violations: List[Dict[str, str]] = []
    for item in file_metrics:
        if _over_limit(
            features["enable_file_lines_check"],
            item.lines,
            thresholds["max_file_physical_lines"],
        ):
            violations.append(
                build_violation(
                    item.file_key,
                    "文件物理行数超限",
                    item.lines,
                    thresholds["max_file_physical_lines"],
                )
            )
        if _over_limit(
            features["enable_function_count_check"],
            item.function_count,
            thresholds["max_function_count_per_file"],
        ):
            violations.append(
                build_violation(
                    item.file_key,
                    "单文件函数数量超限",
                    item.function_count,
                    thresholds["max_function_count_per_file"],
                )
            )
    return violations


def _function_level_violations(function_metrics: List[FunctionMetrics], config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Check per-function physical lines and cognitive complexity."""
    thresholds = config["thresholds"]
    features = config["features"]
    skipped_names = set(config["exclusions"]["function_names"])
    violations: List[Dict[str, str]] = []
    for func in function_metrics:
        if func.name in skipped_names:
            continue
        if _over_limit(
            features["enable_function_lines_check"],
            func.lines,
            thresholds["max_function_physical_lines"],
        ):
            violations.append(
                build_violation(
                    f"{func.file_key}::{func.name}",
                    "函数物理行数超限",
                    func.lines,
                    thresholds["max_function_physical_lines"],
                )
            )
        if _over_limit(
            features["enable_cognitive_complexity_check"],
            func.complexity,
            thresholds["max_cognitive_complexity"],
        ):
            # _over_limit already guarantees complexity is not None
            complexity = func.complexity
            if complexity is None:
                raise RuntimeError("complexity missing after over-limit check")
            violations.append(
                build_violation(
                    f"{func.file_key}::{func.name}",
                    "认知复杂度超限",
                    complexity,
                    thresholds["max_cognitive_complexity"],
                )
            )
    return violations


_GRADE_A_SCORE = 90
_GRADE_B_SCORE = 80
_GRADE_C_SCORE = 70


def health_score(
    file_metrics: List[FileMetrics],
    function_metrics: List[FunctionMetrics],
    violations: List[Dict[str, str]],
) -> Tuple[int, str]:
    """Score overall code health from 0 to 100 and map it to an A-D grade.

    The score starts at 100 and deducts per category penalties per violation.
    Grades follow the industry A-F rubric: A >= 90, B >= 80, C >= 70, else D.

    Args:
        file_metrics: measured per-file metrics.
        function_metrics: measured per-function metrics.
        violations: violation records produced by the four checks.

    Returns:
        (health score, one-letter grade).
    """
    penalty: Dict[str, int] = {
        "文件物理行数超限": 15,
        "单文件函数数量超限": 10,
        "函数物理行数超限": 8,
        "认知复杂度超限": 12,
    }
    score = 100
    for item in violations:
        score = max(0, score - penalty.get(item["issue"], 5))
    if not function_metrics and not file_metrics:
        return score, "-"
    grade = (
        "A" if score >= _GRADE_A_SCORE else "B" if score >= _GRADE_B_SCORE else "C" if score >= _GRADE_C_SCORE else "D"
    )
    return score, grade


def generate_markdown_report(
    file_metrics: List[FileMetrics],
    function_metrics: List[FunctionMetrics],
    violations: List[Dict[str, str]],
    config: Dict[str, Any],
) -> None:
    """Write the Markdown report with health overview and per-file detail.

    Args:
        file_metrics: measured per-file metrics.
        function_metrics: measured per-function metrics.
        violations: violation records produced by the four checks.
        config: full quality-gate configuration (report texts & paths).
    """
    report_cfg = config["report"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score, grade = health_score(file_metrics, function_metrics, violations)
    lines: List[str] = [
        f"# {report_cfg['title']}",
        f"> 生成时间：{now}",
        f"> {report_cfg['description']}",
        "",
        "## 代码健康度概览",
        f"- **健康评分：{score}（等级 {grade}）**",
        "- 评分规则：满分 100，按违规类别扣分（文件行数 -15 / 函数数 -10 / "
        "函数行数 -8 / 认知复杂度 -12），A ≥90 / B ≥80 / C ≥70 / D <70",
        "",
    ]
    complexities = [item.complexity for item in function_metrics if item.complexity is not None]
    total_lines = sum(item.lines for item in file_metrics)
    lines += _overview_rows(file_metrics, function_metrics, complexities, total_lines, violations)
    lines += ["## 阈值配置"] + _threshold_rows(config["thresholds"])

    if violations:
        lines.append(f"## ❌ 违规汇总（{len(violations)}）")
        lines.append("| " + " | ".join(report_cfg["violation_headers"]) + " |")
        lines.append("|---|---|---|---|")
        lines.extend(
            f"| `{item['target']}` | {item['issue']} | {item['current']} | {item['limit']} |" for item in violations
        )
    else:
        lines.append(f"## {report_cfg['pass_text']}")
    lines.append("")

    if report_cfg["show_full_detail"]:
        lines.append("## 📋 全量文件明细")
        for item in file_metrics:
            lines.append(f"### `{item.file_key}`")
            lines.append(f"- 有效行数：{item.lines}")
            lines.append(f"- 函数总数：{item.function_count}")
            lines.append("")
            lines.append("| " + " | ".join(report_cfg["function_headers"]) + " |")
            lines.append("|---|---|---|")
            lines.extend(
                f"| {func.name} | {func.lines} | {_fmt_complexity(func.complexity)} |"
                for func in function_metrics
                if func.file_key == item.file_key
            )
            lines.append("")

    Path(report_cfg["markdown_report_path"]).write_text("\n".join(lines), encoding="utf-8")
    print(f"[INFO] Markdown 报告已生成: {report_cfg['markdown_report_path']}")


def _overview_rows(
    file_metrics: List[FileMetrics],
    function_metrics: List[FunctionMetrics],
    complexities: List[int],
    total_lines: int,
    violations: List[Dict[str, str]],
) -> List[str]:
    """Build the key-metric rows of the health overview table."""
    average = round(sum(complexities) / len(complexities), 1) if complexities else 0.0
    max_complexity = max(complexities) if complexities else 0
    return [
        "| 指标 | 数值 |",
        "|---|---|",
        f"| 扫描文件数 | {len(file_metrics)} |",
        f"| 函数总数 | {len(function_metrics)} |",
        f"| 平均认知复杂度 | {average} |",
        f"| 最高认知复杂度 | {max_complexity} |",
        f"| 代码有效行数（空行/纯注释剔除） | {total_lines} |",
        f"| 违规总数 | {len(violations)} |",
        "",
    ]


def _threshold_rows(thresholds: Dict[str, Any]) -> List[str]:
    """Build the configured-threshold table rows."""
    return [
        f"- 认知复杂度 ≤ {thresholds['max_cognitive_complexity']}",
        f"- 单文件物理行数 ≤ {thresholds['max_file_physical_lines']}",
        f"- 单文件函数数量 ≤ {thresholds['max_function_count_per_file']}",
        f"- 单函数物理行数 ≤ {thresholds['max_function_physical_lines']}",
        "",
    ]


def _fmt_complexity(value: int | None) -> str:
    """Render a complexity value, using '-' when the report lacks it."""
    return str(value) if value is not None else "-"


def main() -> None:
    """Orchestrate config load, metric measurement and gate validation."""
    config = load_config()
    report_path = Path(config["report"]["json_report_path"])
    raw_report = quality_metrics.load_report(report_path)
    complexities = quality_metrics.complexity_map(raw_report)
    line_cfg = config["line_counting"]
    file_metrics, function_metrics = quality_metrics.measure_files(
        config["scan"]["include_paths"],
        count_blank_lines=line_cfg["count_blank_lines"],
        count_comment_lines=line_cfg["count_comment_lines"],
        exclude_patterns=config["exclusions"]["file_patterns"],
    )
    function_metrics = [
        FunctionMetrics(
            file_key=item.file_key,
            name=item.name,
            lines=item.lines,
            complexity=complexities.get((item.file_key, item.name)),
        )
        for item in function_metrics
    ]
    is_pass, violations = validate_quality(file_metrics, function_metrics, config)
    generate_markdown_report(file_metrics, function_metrics, violations, config)
    score, grade = health_score(file_metrics, function_metrics, violations)
    print(f"[INFO] 健康评分：{score}（等级 {grade}）；违规 {len(violations)} 项")
    if not is_pass:
        print(f"\n❌ [QUALITY-GATE-FAIL] {config['report']['fail_text']}")
        sys.exit(1)
    print("✅ [QUALITY-GATE-PASS] 全部质量校验通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
