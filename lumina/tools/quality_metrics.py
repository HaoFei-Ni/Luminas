"""Unified metric layer for the two-tier quality gate.

为两级质量门禁提供统一指标层，避免各入口重复实现与解析漂移：

- tools.ci_quality_gate（CI/手动：全量四项门禁，含 AST 行数统计 + 健康度报告）
- tools.complexity_precommit（提交前：认知复杂度强校验，仅扫本次暂存文件）

收敛三件事：
1. complexipy JSON 多版本 schema 归一化；
2. 行数指标由 Python ``ast`` 原生测量（见 ``py_file_metrics``）；
3. venv 工具定位与扫描范围收敛，供所有入口复用。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.cache_layout import prepare_complexipy_cwd
from tools.py_metric_types import FileMetrics, FunctionMetrics, as_file_key, excluded

__all__ = [
    "FileMetrics",
    "FunctionMetrics",
    "as_file_key",
    "complexity_map",
    "excluded",
    "load_report",
    "measure_files",
    "run_complexipy",
    "venv_executable",
]


def venv_executable(name: str) -> Path:
    """Return the venv-dir path of an executable (``.exe`` suffix on Windows)."""
    suffix = ".exe" if os.name == "nt" else ""
    return Path(sys.executable).with_name(f"{name}{suffix}")


def complexity_map(raw: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    """Normalize complexipy reports of any supported version into a lookup."""
    result: dict[tuple[str, str], int] = {}
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for entry in raw:
        if "file_path" in entry:
            result.update(_group_entries(entry))
        elif "path" in entry and "function_name" in entry:
            key = (as_file_key(entry["path"]), str(entry["function_name"]))
            result[key] = int(entry["complexity"])
        else:
            raise ValueError(f"Unrecognized complexipy report entry: {entry!r}")
    return result


def _group_entries(entry: dict[str, Any]) -> dict[tuple[str, str], int]:
    """Convert one pre-8 group record into a (file, function) complexity map."""
    file_key = as_file_key(entry["file_path"])
    grouped: dict[tuple[str, str], int] = {}
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for func in entry.get("functions", []):
        grouped[(file_key, str(func["function_name"]))] = int(func["cognitive_complexity"])
    return grouped


def run_complexipy(targets: list[str], output_path: Path) -> None:
    """Run a complexipy JSON scan over ``targets`` (paths relative to cwd)."""
    cache_cwd = prepare_complexipy_cwd()
    report = output_path.resolve()
    command = [
        str(venv_executable("complexipy")),
        "--output-format=json",
        f"--output={report}",
        "--failed=false",
        "--quiet=true",
        *[str(Path(target).resolve()) for target in targets],
    ]
    result = subprocess.run(command, cwd=cache_cwd, check=False)  # noqa: S603
    # complexipy 超限亦非零退出，但 JSON 照常产出；是否失败由调用方按阈值决定。
    if not report.exists() or report.stat().st_size == 0:
        raise RuntimeError(f"complexipy failed to produce {report} (exit {result.returncode})")


def load_report(report_path: Path) -> list[dict[str, Any]]:
    """Load and validate the complexipy JSON report file."""
    with report_path.open("r", encoding="utf-8") as handle:
        return list(json.load(handle))


def measure_files(
    paths: list[str],
    *,
    count_blank_lines: bool,
    count_comment_lines: bool,
    exclude_patterns: list[str],
) -> tuple[list[FileMetrics], list[FunctionMetrics]]:
    """Measure line stats via stdlib AST; complexity is attached separately."""
    # 延迟导入：类型在 py_metric_types；测量在 py_file_metrics，避免环。
    from tools.py_file_metrics import measure_files as _measure

    return _measure(
        paths,
        count_blank_lines=count_blank_lines,
        count_comment_lines=count_comment_lines,
        exclude_patterns=exclude_patterns,
    )
