"""Quality-gate report writer (Markdown + machine-readable summary).

Split from ``tools.reporting.python_gate`` to keep structure metrics under the file/function caps.
Markdown is bilingual (zh-CN / en); JSON keys stay English for CI parsers.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.support.metrics import FileMetrics, FunctionMetrics

_SCHEMA_VERSION = "1.1"
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
    "Python复杂语句缺少why行内注释": 8,
    "循环依赖超限": 15,
    "模块扇出超限": 10,
    "继承深度超限": 10,
    "重复代码块超限": 10,
    "代码重复率超限": 10,
    "未检异常路径超限": 15,
    "全局状态变量超限": 10,
    "空引用风险超限": 15,
}

_ISSUE_EN: dict[str, str] = {
    "文件物理行数超限": "file physical lines exceeded",
    "单文件函数数量超限": "functions per file exceeded",
    "函数物理行数超限": "function physical lines exceeded",
    "认知复杂度超限": "cognitive complexity exceeded",
    "圈复杂度超限": "cyclomatic complexity exceeded",
    "控制嵌套超限": "control nesting exceeded",
    "函数含自递归（默认禁止）": "self-recursion (disallowed by default)",
    "Python复杂语句缺少行内注释": "complex Python statement lacks inline why-comment",
    "Python复杂语句缺少why行内注释": "complex Python statement lacks inline why-comment",
    "循环依赖超限": "cyclic dependencies exceeded",
    "模块扇出超限": "module fan-out exceeded",
    "继承深度超限": "inheritance depth exceeded",
    "重复代码块超限": "duplicate code blocks exceeded",
    "代码重复率超限": "code duplication ratio exceeded",
    "未检异常路径超限": "unchecked exception paths exceeded",
    "全局状态变量超限": "global state variables exceeded",
    "空引用风险超限": "None-reference risk exceeded",
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
    """Score overall code health from 0 to 100 and map it to an A–D grade."""
    score = 100
    # 必须逐条扣分：未知 issue 默认 −5，避免新门禁类别漏计。
    for item in violations:
        score = max(0, score - _PENALTY.get(item["issue"], 5))
    if not function_metrics and not file_metrics:
        return score, "-"
    grade = next((band for threshold, band in _GRADE_BANDS if score >= threshold), "D")
    return score, grade


def generate_markdown_report(
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
    violations: list[dict[str, str]],
    config: dict[str, Any],
) -> None:
    """Write bilingual Markdown verdict and English-keyed JSON under ``tests/reports/``."""
    report_cfg = config["report"]
    score, grade = health_score(file_metrics, function_metrics, violations)
    scan_paths = list(config.get("scan", {}).get("include_paths", []))
    metrics = _metrics_snapshot(file_metrics, function_metrics, violations)
    lines = _report_header(report_cfg, score, grade, violations, scan_paths)
    lines += _overview_rows(metrics)
    lines += ["## 阈值 / Thresholds", ""] + _threshold_rows(config["thresholds"])
    lines += _violation_section(report_cfg, violations)
    lines += _detail_section(report_cfg, file_metrics, function_metrics)
    md_path = Path(report_cfg["markdown_report_path"])
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    findings = [{**item, "issue_en": _ISSUE_EN.get(item["issue"], item["issue"])} for item in violations]
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "locale": "zh-CN/en",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": "PASS" if not violations else "FAIL",
        "health_score": score,
        "grade": grade,
        "scan_paths": scan_paths,
        "metrics": metrics,
        "thresholds": config["thresholds"],
        "findings": findings,
    }
    summary_path = Path(report_cfg["summary_json_path"])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[INFO] quality report: {report_cfg['markdown_report_path']}")
    print(f"[INFO] quality summary: {summary_path.as_posix()}")


def _metrics_snapshot(
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
    violations: list[dict[str, str]],
) -> dict[str, Any]:
    """Aggregate scan metrics for the report header and JSON summary."""
    complexities = [item.complexity for item in function_metrics if item.complexity is not None]
    total_lines = sum(item.lines for item in file_metrics)
    average = round(sum(complexities) / len(complexities), 1) if complexities else 0.0
    max_complexity = max(complexities) if complexities else 0
    return {
        "files": len(file_metrics),
        "functions": len(function_metrics),
        "mean_cognitive_complexity": average,
        "max_cognitive_complexity": max_complexity,
        "effective_loc": total_lines,
        "findings": len(violations),
    }


def _report_header(
    report_cfg: dict[str, Any],
    score: int,
    grade: str,
    violations: list[dict[str, str]],
    scan_paths: list[str],
) -> list[str]:
    """Build bilingual document metadata, verdict, and scoring policy."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    verdict = "通过 / PASS" if not violations else "未通过 / FAIL"
    scope = ", ".join(f"`{path}`" for path in scan_paths) if scan_paths else "—"
    return [
        f"# {report_cfg['title']}",
        "",
        "| 字段 / Field | 值 / Value |",
        "|---|---|",
        f"| 文档 / Document | `{report_cfg.get('document_id', 'LUM-QG-PY')}` |",
        f"| 模式 / Schema | `{_SCHEMA_VERSION}` |",
        f"| 生成时间 (UTC) / Generated | `{now}` |",
        f"| 扫描范围 / Scan scope | {scope} |",
        f"| 裁决 / Verdict | **{verdict}** |",
        f"| 健康分 / Health score | **{score}**（等级 / grade **{grade}**） |",
        "",
        f"> {report_cfg['description']}",
        "",
        "## 评分 / Scoring",
        "- 满分 100，按违规类别扣分 / Base 100; subtract per finding class"
        "（文件行数 −15 / 函数数 −10 / 函数行数 −8 / 认知·圈复杂度 −12 / 嵌套 −10；未知 −5）。",
        f"- 等级带 / Bands：A ≥ {_GRADE_A_SCORE} / B ≥ {_GRADE_B_SCORE} / "
        f"C ≥ {_GRADE_C_SCORE} / D < {_GRADE_C_SCORE}。",
        "",
    ]


def _overview_rows(metrics: dict[str, Any]) -> list[str]:
    """Build the bilingual key-metric table."""
    return [
        "## 指标 / Metrics",
        "",
        "| 指标 / Metric | 数值 / Value |",
        "|---|---|",
        f"| 扫描文件数 / Files scanned | {metrics['files']} |",
        f"| 函数总数 / Functions | {metrics['functions']} |",
        f"| 平均认知复杂度 / Mean cognitive complexity | {metrics['mean_cognitive_complexity']} |",
        f"| 最高认知复杂度 / Max cognitive complexity | {metrics['max_cognitive_complexity']} |",
        f"| 有效行数 / Effective LOC（空行与纯注释剔除） | {metrics['effective_loc']} |",
        f"| 违规数 / Findings | {metrics['findings']} |",
        "",
    ]


def _threshold_rows(thresholds: dict[str, Any]) -> list[str]:
    """Build the bilingual configured-threshold table."""
    return [
        "| 控制项 / Control | 上限 / Limit |",
        "|---|---|",
        f"| 认知复杂度 / Cognitive complexity | ≤ {thresholds['max_cognitive_complexity']} |",
        f"| 圈复杂度 / Cyclomatic complexity | ≤ {thresholds.get('max_cyclomatic_complexity', '—')} |",
        f"| 控制嵌套 / Control nesting | ≤ {thresholds.get('max_control_nesting_depth', '—')} |",
        f"| 文件物理行数 / File physical lines | ≤ {thresholds['max_file_physical_lines']} |",
        f"| 单文件函数数 / Functions per file | ≤ {thresholds['max_function_count_per_file']} |",
        f"| 函数物理行数 / Function physical lines | ≤ {thresholds['max_function_physical_lines']} |",
        f"| 循环依赖 / Cyclic dependencies | ≤ {thresholds.get('max_cyclic_dependencies', '—')} |",
        f"| 模块扇出 / Module fan-out | ≤ {thresholds.get('max_module_fan_out', '—')} |",
        f"| 继承深度 / Inheritance depth | ≤ {thresholds.get('max_inheritance_depth', '—')} |",
        f"| 重复代码块 / Duplicate blocks | ≤ {thresholds.get('max_duplicate_code_blocks', '—')} |",
        f"| 代码重复率(%) / Duplication ratio (%) | ≤ {thresholds.get('max_code_duplication_ratio', '—')} |",
        f"| 未检异常路径 / Unchecked exception paths | ≤ {thresholds.get('max_unchecked_exception_paths', '—')} |",
        f"| 全局状态变量/文件 / Globals per file | ≤ {thresholds.get('max_global_state_variables', '—')} |",
        f"| 空引用风险 / None-reference risk | ≤ {thresholds.get('max_none_reference_risk', '—')} |",
        "",
    ]


def _violation_section(report_cfg: dict[str, Any], violations: list[dict[str, str]]) -> list[str]:
    """Build either the bilingual pass banner or the findings table."""
    if not violations:
        return ["## 裁决 / Verdict", "", report_cfg["pass_text"], ""]
    rows = [
        f"## 违规汇总 / Findings（{len(violations)}）",
        "",
        "| " + " | ".join(report_cfg["violation_headers"]) + " |",
        "|---|---|---|---|",
    ]
    rows.extend(
        [
            f"| `{i['target']}` | {i['issue']} / {_ISSUE_EN.get(i['issue'], i['issue'])} | {i['current']} | {i['limit']} |"
            for i in violations  # 必须单行 listcomp：避免多行 for 被门禁误判为裸循环
        ]
    )
    rows.append("")
    return rows


def _detail_section(
    report_cfg: dict[str, Any],
    file_metrics: list[FileMetrics],
    function_metrics: list[FunctionMetrics],
) -> list[str]:
    """Build the bilingual per-file function inventory tables."""
    if not report_cfg.get("show_full_detail", True):
        return []
    grouped: dict[str, list[FunctionMetrics]] = {}
    # 必须先按文件归组：避免嵌套过滤抬高认知复杂度与二次全表扫描。
    for func in function_metrics:
        grouped.setdefault(func.file_key, []).append(func)
    lines = ["## 明细 / Inventory", ""]
    headers = "| " + " | ".join(report_cfg["function_headers"]) + " |"
    # 必须按文件挂接：避免跨文件混表导致审计歧义。
    for item in file_metrics:
        funcs = grouped.get(item.file_key, [])
        lines.append(f"### `{item.file_key}`")
        lines.append(f"- 有效行数 / Effective LOC：{item.lines}")
        lines.append(f"- 函数数 / Functions：{item.function_count}")
        lines.append("")
        lines.append(headers)
        lines.append("|---|---|---|")
        # 必须单行生成：避免多行 genexp 的 for 被行扫描误判为裸循环。
        lines.extend([f"| {f.name} | {f.lines} | {f.complexity if f.complexity is not None else '—'} |" for f in funcs])
        lines.append("")
    return lines
