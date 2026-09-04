"""AST-based Python file/function line and structure measurement.

从 ``quality_metrics`` 拆出，避免单文件函数数与 ``measure_files`` 行数超限。
"""

from __future__ import annotations

import ast
from pathlib import Path

from tools.py_metric_types import FileMetrics, FunctionMetrics, as_file_key, excluded
from tools.py_recursion import self_recursive_names
from tools.py_structure_metrics import measure_function


def measure_files(
    paths: list[str],
    *,
    count_blank_lines: bool,
    count_comment_lines: bool,
    exclude_patterns: list[str],
) -> tuple[list[FileMetrics], list[FunctionMetrics]]:
    """Measure line stats via stdlib AST; complexity is attached separately."""
    files = collect_python_files(paths, exclude_patterns)
    file_metrics: list[FileMetrics] = []
    function_metrics: list[FunctionMetrics] = []
    # 单遍：逐文件测量，避免跨文件状态污染指标。
    for file_path in files:
        file_m, func_m = _measure_one(file_path, count_blank_lines, count_comment_lines)
        file_metrics.append(file_m)
        function_metrics.extend(func_m)
    return file_metrics, function_metrics


def collect_python_files(paths: list[str], exclude_patterns: list[str]) -> list[Path]:
    """Collect sorted, de-duplicated ``*.py`` files under paths or as files."""
    collected: list[Path] = []
    # 单遍：文件/目录两种入口统一进列表再去重排序。
    for raw in paths:
        collected.extend(_paths_from(Path(raw)))
    return sorted({path for path in collected if not excluded(as_file_key(path), exclude_patterns)})


def count_significant(lines: list[str], count_blank_lines: bool, count_comment_lines: bool) -> int:
    """Count lines that count as physical lines under the current toggles."""
    return sum(1 for line in lines if _is_counted(line.strip(), count_blank_lines, count_comment_lines))


def _paths_from(candidate: Path) -> list[Path]:
    """Expand one path argument into zero or more ``*.py`` files."""
    if candidate.is_file() and candidate.suffix == ".py":
        return [candidate]
    if candidate.is_dir():
        return list(candidate.rglob("*.py"))
    return []


def _measure_one(
    file_path: Path,
    count_blank_lines: bool,
    count_comment_lines: bool,
) -> tuple[FileMetrics, list[FunctionMetrics]]:
    """Measure one Python source file into file + function metrics."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    raw_lines = source.splitlines()
    file_key = as_file_key(file_path)
    recursive = self_recursive_names(tree)
    # 单遍 walk：须收齐嵌套 def，避免函数计数低估。
    fn_nodes = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    file_metrics = FileMetrics(
        file_key=file_key,
        path=str(file_path),
        lines=count_significant(raw_lines, count_blank_lines, count_comment_lines),
        function_count=len(fn_nodes),
    )
    functions = [
        _function_metric(node, file_key, raw_lines, recursive, count_blank_lines, count_comment_lines)
        for node in fn_nodes  # 须挂结构指标，避免后续门禁读空 cyclomatic。
    ]
    return file_metrics, functions


def _function_metric(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    file_key: str,
    raw_lines: list[str],
    recursive: set[str],
    count_blank_lines: bool,
    count_comment_lines: bool,
) -> FunctionMetrics:
    """Build FunctionMetrics for one AST function/async function node."""
    start = node.lineno
    end = node.end_lineno or node.lineno
    body = raw_lines[start - 1 : end]
    structure = measure_function(node)
    return FunctionMetrics(
        file_key=file_key,
        name=node.name,
        lines=count_significant(body, count_blank_lines, count_comment_lines),
        complexity=None,
        has_recursion=node.name in recursive,
        cyclomatic=structure.cyclomatic,
        control_nesting=structure.control_nesting,
    )


def _is_counted(stripped: str, count_blank_lines: bool, count_comment_lines: bool) -> bool:
    """Decide whether one stripped line counts as a physical line."""
    if not stripped:
        return count_blank_lines
    if stripped.startswith("#"):
        return count_comment_lines
    return True
