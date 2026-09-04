"""Markdown health report for the Python quality gate.

从 ``ci_quality_gate`` 拆出，避免单文件函数数与报告函数行数超限。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.quality_metrics import FileMetrics, FunctionMetrics

_GRADE_A_SCORE = 90
_GRADE_B_SCORE = 80
_GRADE_C_SCORE = 70

_PENALTY: dict[str, int] = {
    "文件物理行数超限": 15,
    "单文件函数数量超限": 10,
    "函数物理行数超限": 8,
    "认知复杂度超限": 12,
    "圈复杂度超限": 12,
    "控制嵌套超限": 10,
    "函数含自递归（默认禁止）": 12,
    "Python复杂语句缺少行内注释": 8,
    "循环依赖超限": 15,
    "模块扇出超限": 10,
    "继承深度超限": 10,
    "重复代码块超限": 10,
    "代码重复率超限": 10,
    "未检异常路径超限": 15,
    "全局状态变量超限": 10,
    "空引用风险超限": 15,
}

_GRADE_BANDS: tuple[tuple[int, str], ...] = (
    (_GRADE_A_SCORE, "A"),
    (_GRADE_B_SCORE, "B"),
    (_GRADE_C_SCORE, "C"),
)


def health_score(
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
    violations: list[dict[str, str]],
) -> tuple[int, str]:
    """Score overall code health from 0 to 100 and map it to an A-D grade."""
    score = 100
    # 单遍扣分：未知 issue 默认 -5，避免新门禁类别漏计。
    for item in violations:
        score = max(0, score - _PENALTY.get(item["issue"], 5))
    if not function_metrics and not file_metrics:
        return score, "-"
    return score, _grade_for(score)


def generate_markdown_report(
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
    violations: list[dict[str, str]],
    config: dict[str, Any],
) -> None:
    """Write the Markdown report with health overview and per-file detail."""
    report_cfg = config["report"]
    score, grade = health_score(file_metrics, function_metrics, violations)
    complexities = [item.complexity for item in function_metrics if item.complexity is not None]
    total_lines = sum(item.lines for item in file_metrics)
    lines = _report_header(report_cfg, score, grade)
    lines += _overview_rows(file_metrics, function_metrics, complexities, total_lines, violations)
    lines += ["## 阈值配置"] + _threshold_rows(config["thresholds"])
    lines += _violation_section(report_cfg, violations)
    if report_cfg["show_full_detail"]:
        lines += _detail_section(report_cfg, file_metrics, function_metrics)
    Path(report_cfg["markdown_report_path"]).write_text("\n".join(lines), encoding="utf-8")
    print(f"[INFO] Markdown 报告已生成: {report_cfg['markdown_report_path']}")


def _grade_for(score: int) -> str:
    """Map a numeric score to A/B/C/D via descending bands."""
    # 单遍：首个命中即返回，避免嵌套三元抬高认知复杂度。
    for threshold, grade in _GRADE_BANDS:
        if score >= threshold:
            return grade
    return "D"


def _report_header(report_cfg: dict[str, Any], score: int, grade: str) -> list[str]:
    """Build title, timestamp, and health-overview preamble."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        f"# {report_cfg['title']}",
        f"> 生成时间：{now}",
        f"> {report_cfg['description']}",
        "",
        "## 代码健康度概览",
        f"- **健康评分：{score}（等级 {grade}）**",
        "- 评分规则：满分 100，按违规类别扣分（文件行数 -15 / 函数数 -10 / "
        "函数行数 -8 / 认知·圈复杂度 -12 / 嵌套 -10），A ≥90 / B ≥80 / C ≥70 / D <70",
        "",
    ]


def _overview_rows(
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
    complexities: list[int],
    total_lines: int,
    violations: list[dict[str, str]],
) -> list[str]:
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


def _threshold_rows(thresholds: dict[str, Any]) -> list[str]:
    """Build the configured-threshold table rows."""
    return [
        f"- 认知复杂度 ≤ {thresholds['max_cognitive_complexity']}",
        f"- 圈复杂度 ≤ {thresholds.get('max_cyclomatic_complexity', '-')}",
        f"- 控制嵌套 ≤ {thresholds.get('max_control_nesting_depth', '-')}",
        f"- 单文件物理行数 ≤ {thresholds['max_file_physical_lines']}",
        f"- 单文件函数数量 ≤ {thresholds['max_function_count_per_file']}",
        f"- 单函数物理行数 ≤ {thresholds['max_function_physical_lines']}",
        f"- 循环依赖 ≤ {thresholds.get('max_cyclic_dependencies', '-')}",
        f"- 模块扇出 ≤ {thresholds.get('max_module_fan_out', '-')}",
        f"- 继承深度 ≤ {thresholds.get('max_inheritance_depth', '-')}",
        f"- 重复代码块 ≤ {thresholds.get('max_duplicate_code_blocks', '-')}",
        f"- 代码重复率(%) ≤ {thresholds.get('max_code_duplication_ratio', '-')}",
        f"- 未检异常路径 ≤ {thresholds.get('max_unchecked_exception_paths', '-')}",
        f"- 全局状态变量/文件 ≤ {thresholds.get('max_global_state_variables', '-')}",
        f"- 空引用风险 ≤ {thresholds.get('max_none_reference_risk', '-')}",
        "",
    ]


def _violation_section(report_cfg: dict[str, Any], violations: list[dict[str, str]]) -> list[str]:
    """Build either the pass banner or the violation table."""
    if not violations:
        return [f"## {report_cfg['pass_text']}", ""]
    rows = [
        f"## ❌ 违规汇总（{len(violations)}）",
        "| " + " | ".join(report_cfg["violation_headers"]) + " |",
        "|---|---|---|---|",
    ]
    rows.extend(
        f"| `{item['target']}` | {item['issue']} | {item['current']} | {item['limit']} |"
        # 单遍：逐条写入，避免汇总丢失定位。
        for item in violations
    )
    rows.append("")
    return rows


def _detail_section(
    report_cfg: dict[str, Any],
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
) -> list[str]:
    """Build the per-file function detail tables."""
    lines = ["## 📋 全量文件明细"]
    # 单遍：按文件挂接函数行，避免跨文件混表。
    for item in file_metrics:
        lines.append(f"### `{item.file_key}`")
        lines.append(f"- 有效行数：{item.lines}")
        lines.append(f"- 函数总数：{item.function_count}")
        lines.append("")
        lines.append("| " + " | ".join(report_cfg["function_headers"]) + " |")
        lines.append("|---|---|---|")
        lines.extend(
            f"| {func.name} | {func.lines} | {func.complexity if func.complexity is not None else '-'} |"
            # 单遍：只取本文件函数，避免全表过滤后二次扫描。
            for func in function_metrics
            if func.file_key == item.file_key
        )
        lines.append("")
    return lines
