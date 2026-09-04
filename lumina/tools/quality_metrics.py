"""Unified metric layer for the two-tier quality gate.

为两级质量门禁提供统一指标层，避免各入口重复实现与解析漂移：

- tools.ci_quality_gate（CI/手动：全量四项门禁，含 AST 行数统计 + 健康度报告）
- tools.complexity_precommit（提交前：认知复杂度强校验，仅扫本次暂存文件）

收敛三件事：
1. complexipy JSON 多版本 schema 归一化：≤7 为按文件分组（file_path /
   functions[{function_name, cognitive_complexity}]），8+ 为扁平逐函数
   （path / function_name / complexity）。统一映射为 (file_key, name) → int。
2. 行数指标由 Python ``ast`` 原生测量，与 complexipy 版本彻底解耦
   （complexipy 8 起不再输出任何行数信息）。
3. venv 工具定位与扫描范围收敛，供所有入口复用。
"""

from __future__ import annotations

import ast
import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.py_recursion import self_recursive_names


@dataclass(frozen=True)
class FunctionMetrics:
    """Per-function metrics: AST lines, optional complexity, self-recursion."""

    file_key: str
    name: str
    lines: int
    complexity: int | None
    has_recursion: bool = False


@dataclass(frozen=True)
class FileMetrics:
    """Per-file metrics measured from AST (complexipy 8 no longer reports them)."""

    file_key: str
    path: str
    lines: int
    function_count: int


def as_file_key(path: str | Path) -> str:
    """Normalize a path to a forward-slash key comparable across schemas."""
    return Path(path).as_posix()


def venv_executable(name: str) -> Path:
    """Return the venv-dir path of an executable (``.exe`` suffix on Windows)."""
    suffix = ".exe" if os.name == "nt" else ""
    return Path(sys.executable).with_name(f"{name}{suffix}")


def excluded(file_key: str, patterns: list[str]) -> bool:
    """Return True when a forward-slash key matches any fnmatch pattern."""
    return any(fnmatch.fnmatch(file_key, pattern) for pattern in patterns)


def complexity_map(raw: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    """Normalize complexipy reports of any supported version into a lookup.

    The returned mapping key is (file_key, function_name); the value is the
    cognitive complexity. Entries that match neither the group nor the flat
    schema raise ValueError so schema drift fails loudly instead of silently.

    Args:
        raw: complexipy JSON payload (list of file/function records).

    Returns:
        Lookup mapping (file_key, function_name) to cognitive complexity.

    Raises:
        ValueError: when a record matches no known complexipy schema.
    """
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
    """Run a complexipy JSON scan over ``targets`` (paths relative to cwd).

    The full data set (not just over-threshold functions) is requested so
    downstream scripts decide the pass/fail verdict from a single source.

    Args:
        targets: file/dir paths scanned by complexipy.
        output_path: JSON report destination.

    Raises:
        RuntimeError: when complexipy fails to produce the JSON report.
    """
    command = [
        str(venv_executable("complexipy")),
        "--output-format=json",
        f"--output={output_path}",
        "--failed=false",
        "--quiet=true",
        *targets,
    ]
    result = subprocess.run(command, check=False)  # noqa: S603
    # complexipy 在存在超限函数时同样以非零码退出，但 JSON 数据照常产出；
    # 是否判失败由调用方（门禁/提交钩子）按 quality-gate.toml 阈值决定，
    # 因此这里仅校验报告确实生成，不把退出码当作失败信号。
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"complexipy failed to produce {output_path} (exit {result.returncode})")


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
    """Measure line stats via stdlib AST; complexity is attached separately.

    ``exclude_patterns`` match against forward-slash keys. Blank and pure-comment
    lines count as physical lines only when the corresponding toggle is True.

    Args:
        paths: files/dirs to scan.
        count_blank_lines: count blank lines as physical lines.
        count_comment_lines: count pure-comment lines as physical lines.
        exclude_patterns: fnmatch patterns of files to skip.

    Returns:
        (per-file metrics, per-function metrics without complexity yet).
    """
    files = _collect_python_files(paths, exclude_patterns)
    file_metrics: list[FileMetrics] = []
    function_metrics: list[FunctionMetrics] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        raw_lines = source.splitlines()
        file_key = as_file_key(file_path)
        total = _count_significant(raw_lines, count_blank_lines, count_comment_lines)
        spans = _function_spans(tree)
        recursive = self_recursive_names(tree)
        file_metrics.append(
            FileMetrics(
                file_key=file_key,
                path=str(file_path),
                lines=total,
                function_count=len(spans),
            )
        )
        # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
        for name, start, end in spans:
            body = raw_lines[start - 1 : end]
            function_metrics.append(
                FunctionMetrics(
                    file_key=file_key,
                    name=name,
                    lines=_count_significant(body, count_blank_lines, count_comment_lines),
                    complexity=None,
                    has_recursion=name in recursive,
                )
            )
    return file_metrics, function_metrics


def _collect_python_files(paths: list[str], exclude_patterns: list[str]) -> list[Path]:
    """Collect sorted, de-duplicated ``*.py`` files under paths or as files."""
    collected: list[Path] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for raw in paths:
        candidate = Path(raw)
        if candidate.is_file():
            if candidate.suffix == ".py":
                collected.append(candidate)
        elif candidate.is_dir():
            collected.extend(candidate.rglob("*.py"))
    return sorted({file_path for file_path in collected if not excluded(as_file_key(file_path), exclude_patterns)})


def _function_spans(tree: ast.AST) -> list[tuple[str, int, int]]:
    """Collect (name, start_line, end_line) for every function definition."""
    return [
        (node.name, node.lineno, node.end_lineno or node.lineno)
        # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _count_significant(lines: list[str], count_blank_lines: bool, count_comment_lines: bool) -> int:
    """Count lines that count as physical lines under the current toggles."""
    return sum(1 for line in lines if _is_counted(line.strip(), count_blank_lines, count_comment_lines))


def _is_counted(stripped: str, count_blank_lines: bool, count_comment_lines: bool) -> bool:
    """Decide whether one stripped line counts as a physical line."""
    if not stripped:
        return count_blank_lines
    if stripped.startswith("#"):
        return count_comment_lines
    return True
