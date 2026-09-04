"""C/C++/CUDA structure gate: size + loops + recursion + comment policy.

Comment policy (see quality-gate.toml ``[comment_standard]``):
- file banner required
- every function definition needs a leading why-doc
- every header prototype needs a leading why-doc
"""

from __future__ import annotations

import fnmatch
import sys
import tomllib
from pathlib import Path
from typing import Any

from tools.c_doc_comments import undocumented_prototypes
from tools.c_quality_metrics import CFileMetrics, CFunctionMetrics, measure_c_files


def load_config(config_path: str = "quality-gate.toml") -> dict[str, Any]:
    """Load quality-gate.toml from the lumina working directory."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with path.open("rb") as handle:
        return dict(tomllib.load(handle))


def validate_c(
    files: list[CFileMetrics],
    functions: list[CFunctionMetrics],
    config: dict[str, Any],
) -> list[dict[str, str]]:
    """Return violation records for enabled C size / loop / recursion / doc checks."""
    violations: list[dict[str, str]] = []
    violations.extend(_file_violations(files, config))
    violations.extend(_doc_file_violations(files, config))
    violations.extend(_function_violations(functions, config))
    return violations


def _file_violations(files: list[CFileMetrics], config: dict[str, Any]) -> list[dict[str, str]]:
    """Check per-file line and function-count limits."""
    thresholds = config["c_thresholds"]
    features = config["c_features"]
    violations: list[dict[str, str]] = []
    for item in files:
        limit = thresholds["max_header_physical_lines"] if item.is_header else thresholds["max_impl_physical_lines"]
        if features["enable_file_lines_check"] and item.lines > limit:
            kind = "头文件" if item.is_header else "实现文件"
            violations.append(_violation(item.file_key, f"C{kind}物理行数超限", item.lines, limit))
        max_funcs = thresholds["max_functions_per_file"]
        if features["enable_function_count_check"] and item.function_count > max_funcs:
            violations.append(_violation(item.file_key, "C单文件函数数量超限", item.function_count, max_funcs))
    return violations


def _doc_file_violations(files: list[CFileMetrics], config: dict[str, Any]) -> list[dict[str, str]]:
    """Check file banners and header prototype documentation."""
    features = config["c_features"]
    violations: list[dict[str, str]] = []
    for item in files:
        if features.get("enable_file_banner_check", True) and not item.has_file_banner:
            violations.append(_violation(item.file_key, "C文件缺少文件头文档注释", 0, 1))
        if item.is_header and features.get("enable_header_decl_doc_check", True):
            lines = Path(item.path).read_text(encoding="utf-8", errors="replace").splitlines()
            for name, line in undocumented_prototypes(lines):
                target = f"{item.file_key}::{name}@{line}"
                violations.append(_violation(target, "C头文件声明缺少前置文档注释", 0, 1))
    return violations


def _function_violations(
    functions: list[CFunctionMetrics],
    config: dict[str, Any],
) -> list[dict[str, str]]:
    """Check per-function size, loops, nesting, recursion, and doc comments."""
    features = config["c_features"]
    thresholds = config["c_thresholds"]
    exclusions = config.get("c_exclusions", {})
    violations: list[dict[str, str]] = []
    for func in functions:
        violations.extend(_one_function_violations(func, features, thresholds, exclusions))
    return violations


def _one_function_violations(
    func: CFunctionMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
    exclusions: dict[str, Any],
) -> list[dict[str, str]]:
    """Collect all enabled violations for a single C/CUDA function."""
    target = f"{func.file_key}::{func.name}"
    out: list[dict[str, str]] = []
    if features["enable_function_lines_check"] and func.lines > thresholds["max_function_physical_lines"]:
        out.append(_violation(target, "C函数物理行数超限", func.lines, thresholds["max_function_physical_lines"]))
    allowed = _loops_allowed(func, exclusions)
    loop_limit = thresholds.get("max_loop_count_per_function", 0)
    if features.get("enable_loop_check", True) and not allowed and func.loop_count > loop_limit:
        out.append(_violation(target, "C函数含循环（默认禁止）", func.loop_count, loop_limit))
    nest_limit = thresholds["max_loop_nesting_depth"]
    if features.get("enable_loop_nesting_check", True) and func.loop_nesting > nest_limit:
        out.append(_violation(target, "C函数循环嵌套超限（禁止双层及以上）", func.loop_nesting, nest_limit))
    recur_ok = set(exclusions.get("recursion_allowed_functions", []))
    if features.get("enable_recursion_check", True) and func.has_recursion and func.name not in recur_ok:
        out.append(_violation(target, "C函数含自递归（默认禁止）", 1, 0))
    doc_ok = set(exclusions.get("doc_comment_exempt_functions", []))
    if features.get("enable_function_doc_check", True) and not func.has_doc_comment and func.name not in doc_ok:
        out.append(_violation(target, "C函数缺少前置文档注释", 0, 1))
    return out


def _loops_allowed(func: CFunctionMetrics, exclusions: dict[str, Any]) -> bool:
    """Return True when this function may contain necessary single-level loops."""
    if func.name in set(exclusions.get("loop_allowed_functions", [])):
        return True
    patterns = list(exclusions.get("loop_allowed_file_patterns", []))
    return any(fnmatch.fnmatch(func.file_key, pattern) for pattern in patterns)


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """Build one normalized C-gate violation record."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


def main() -> int:
    """Run the C/CUDA structure gate and print a compact verdict."""
    config = load_config()
    if "c_scan" not in config:
        print("[INFO] quality-gate.toml 无 [c_scan]，跳过 C 门禁")
        return 0
    files, functions = measure_c_files(
        list(config["c_scan"]["include_paths"]),
        list(config.get("c_exclusions", {}).get("file_patterns", [])),
    )
    violations = validate_c(files, functions, config)
    print(f"[INFO] C 扫描文件 {len(files)}，函数 {len(functions)}，违规 {len(violations)}")
    for item in violations:
        print(f"  - {item['target']}: {item['issue']} {item['current']}>{item['limit']}")
    if violations:
        print("❌ [C-QUALITY-GATE-FAIL] C/CUDA 结构度量未通过")
        return 1
    print("✅ [C-QUALITY-GATE-PASS] C/CUDA 结构度量通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
