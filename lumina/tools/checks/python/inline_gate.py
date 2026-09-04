"""Python 侧复杂语句行内注释门禁（由 comment_standard 驱动）.

从 ``ci_quality_gate`` 拆出，避免单文件函数数超过阈值。
L0：邻接 ``#`` 存在即可；L4：``why_include_file_patterns`` 命中时要求 why 线索。
"""

from __future__ import annotations

import ast
import fnmatch
from pathlib import Path
from typing import Any

from tools.checks.comments.comments import uncommented_complex_py_lines
from tools.support import metrics as quality_metrics


def python_inline_complex_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Flag Python for/while lines that lack an adjacent ``#`` why-comment."""
    standard = config.get("comment_standard", {})
    if not standard.get("require_inline_on_complex", False):
        return []
    skip_names = set(config.get("exclusions", {}).get("function_names", []))
    inline_skip = list(standard.get("inline_exclude_file_patterns", ["theory/**", "tests/**"]))
    why_on = bool(standard.get("require_why_semantics", False))
    why_pats = list(standard.get("why_include_file_patterns", ["**"]))
    files = _listed_files(config)
    violations: list[dict[str, str]] = []
    # 单遍：仅扫生产文件，避免 tests 故意裸循环误杀。
    for item in files:
        if _matched(item.file_key, inline_skip):
            continue
        require_why = why_on and _matched(item.file_key, why_pats)
        violations.extend(_file_violations(Path(item.path), item.file_key, skip_names, require_why))
    return violations


def _listed_files(config: dict[str, Any]) -> list[Any]:
    """Collect Python files under scan roots with standard exclusions."""
    files, _ = quality_metrics.measure_files(
        list(config["scan"]["include_paths"]),
        count_blank_lines=False,
        count_comment_lines=False,
        exclude_patterns=list(config.get("exclusions", {}).get("file_patterns", [])),
    )
    return files


def _matched(file_key: str, patterns: list[str]) -> bool:
    """Return True when file_key matches any pattern; ``**`` matches all."""
    if any(pat in {"**", "**/*", "*"} for pat in patterns):
        return True
    return any(fnmatch.fnmatch(file_key, pat) for pat in patterns)


def _file_violations(
    path: Path,
    file_key: str,
    skip_names: set[str],
    require_why: bool,
) -> list[dict[str, str]]:
    """Scan one file's functions for unmarked / non-why complex loops."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    raw = source.splitlines()
    issue = "Python复杂语句缺少why行内注释" if require_why else "Python复杂语句缺少行内注释"
    out: list[dict[str, str]] = []
    # 单遍：只处理函数节点，避免类体/模块级误报。
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        record = _function_inline_violation(node, file_key, raw, skip_names, issue, require_why)
        if record:
            out.append(record)
    return out


def _function_inline_violation(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    file_key: str,
    raw: list[str],
    skip_names: set[str],
    issue: str,
    require_why: bool,
) -> dict[str, str] | None:
    """Return one violation record for a function missing inline why-comments."""
    if node.name in skip_names:
        return None
    start = node.lineno
    end = node.end_lineno or start
    missing = uncommented_complex_py_lines(raw[start - 1 : end], require_why=require_why)
    if not missing:
        return None
    return {
        "target": f"{file_key}::{node.name}",
        "issue": issue,
        "current": str(len(missing)),
        "limit": "0",
    }
