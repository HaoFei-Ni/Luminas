#!/usr/bin/env python3
"""Full quality gate: structure checks plus a health-overview Markdown report.

本执行器为「全量质量门禁」的 CI/本地手动入口（提交前的秒级认知复杂度
强校验见 complexity_precommit.py）。职责：

1. 读取 quality-gate.toml（阈值/开关/排除/报告文案）。
2. 复杂度取自 complexipy JSON（多版本 schema 由 quality_metrics 归一化）；
   行数 / 圈复杂度 / 控制嵌套用 Python AST 原生测量。
3. 执行校验：文件行数、函数数量、函数行数、认知复杂度、圈复杂度、控制嵌套、递归、行内注释、架构（环/扇出/继承/克隆）。
4. 生成对齐行业结构的 Markdown 报告：代码健康度概览 + 违规汇总 + 全量明细。

依赖扫描链（工作目录须为 lumina/）：
    uv run complexipy && uv run python -m tools.reporting.python_gate
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

from tools.checks.architecture.gate import architecture_violations
from tools.checks.python.function_gate import function_structure_violations
from tools.checks.python.inline_gate import python_inline_complex_violations
from tools.checks.reliability.gate import ha_violations
from tools.reporting.report import generate_markdown_report, health_score
from tools.support import metrics as quality_metrics
from tools.support.metrics import FileMetrics, FunctionMetrics


def load_config(config_path: str = "quality-gate.toml") -> dict[str, Any]:
    """Load and parse the quality-gate TOML configuration file."""
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with config_file.open("rb") as handle:
        return dict(tomllib.load(handle))


def build_violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """Build a single normalized violation record for reporting."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


def validate_quality(
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
    config: dict[str, Any],
) -> tuple[bool, list[dict[str, str]]]:
    """Run every enabled quality check over the measured metrics."""
    violations = _file_level_violations(file_metrics, config)
    violations.extend(function_structure_violations(function_metrics, config))
    # [comment_standard].require_inline_on_complex：Python 循环须贴身 # 注释。
    violations.extend(python_inline_complex_violations(config))
    # [features].enable_architecture_check：扇出/环/继承/克隆。
    violations.extend(architecture_violations(config))
    # [features].enable_ha_check：未检异常/全局状态/空引用。
    violations.extend(ha_violations(config))
    return not violations, violations


def _over_limit(enabled: bool, value: int | None, limit: int) -> bool:
    """Return True when a check is enabled and a measured value exceeds its limit."""
    return enabled and value is not None and value > limit


def _file_level_violations(file_metrics: list[FileMetrics], config: dict[str, Any]) -> list[dict[str, str]]:
    """Check per-file physical lines and per-file function counts."""
    thresholds = config["thresholds"]
    features = config["features"]
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for item in file_metrics:
        if _over_limit(features["enable_file_lines_check"], item.lines, thresholds["max_file_physical_lines"]):
            violations.append(
                build_violation(item.file_key, "文件物理行数超限", item.lines, thresholds["max_file_physical_lines"])
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
            has_recursion=item.has_recursion,
            cyclomatic=item.cyclomatic,
            control_nesting=item.control_nesting,
        )
        # 单遍：把 complexipy 认知复杂度挂到 AST 行数/结构指标上。
        for item in function_metrics
    ]
    is_pass, violations = validate_quality(file_metrics, function_metrics, config)
    generate_markdown_report(file_metrics, function_metrics, violations, config)
    score, grade = health_score(file_metrics, function_metrics, violations)
    print(f"[INFO] health={score} grade={grade} findings={len(violations)}")
    if not is_pass:
        print(f"[FAIL] python-structure: {config['report']['fail_text']}")
        sys.exit(1)
    print("[PASS] python-structure")
    sys.exit(0)


if __name__ == "__main__":
    main()
