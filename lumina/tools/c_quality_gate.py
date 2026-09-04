"""C/C++/CUDA 结构门禁入口：尺寸 + 循环 + 递归 + 注释策略.

注释策略真值源：``quality-gate.toml`` 的 ``[comment_standard]``（接入本模块）。
``[c_features]`` 中的文档开关与之对齐；``require_inline_on_complex`` 检查复杂行行内注释。

本文件只编排阈值比对；测量逻辑在 ``c_quality_metrics``。
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
    """从 lumina 工作目录加载质量门禁 TOML；缺失则直接退出."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with path.open("rb") as handle:
        return dict(tomllib.load(handle))


def comment_features(config: dict[str, Any]) -> dict[str, Any]:
    """合并 ``[comment_standard]`` 到 C 文档/行内相关 feature 开关.

    原先 ``[comment_standard]`` 是死配置；此处为唯一接线，避免双源漂移。
    """
    features = dict(config.get("c_features", {}))
    standard = config.get("comment_standard", {})
    if not standard:
        return features
    features["enable_file_banner_check"] = bool(standard.get("require_file_banner", True))
    features["enable_function_doc_check"] = bool(standard.get("require_function_doc", True))
    features["enable_header_decl_doc_check"] = bool(standard.get("require_header_decl_doc", True))
    features["enable_inline_complex_check"] = bool(standard.get("require_inline_on_complex", False))
    features["enable_why_semantics"] = bool(standard.get("require_why_semantics", False))
    return features


def why_include_patterns(config: dict[str, Any]) -> list[str]:
    """L4 作用路径；``require_why_semantics`` 关闭时返回空（仅 L0 存在性）."""
    standard = config.get("comment_standard", {})
    if not standard.get("require_why_semantics", False):
        return []
    return list(standard.get("why_include_file_patterns", ["**"]))


def validate_c(
    files: list[CFileMetrics],
    functions: list[CFunctionMetrics],
    config: dict[str, Any],
) -> list[dict[str, str]]:
    """汇总文件级、文档级、函数级违规记录."""
    violations: list[dict[str, str]] = []
    violations.extend(_file_violations(files, config))
    violations.extend(_doc_file_violations(files, config))
    violations.extend(_function_violations(functions, config))
    return violations


def _file_violations(files: list[CFileMetrics], config: dict[str, Any]) -> list[dict[str, str]]:
    """校验单文件物理行数与函数个数上限."""
    thresholds = config["c_thresholds"]
    features = config["c_features"]
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
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
    """校验文件 banner 与头文件原型文档（开关来自 comment_standard）."""
    features = comment_features(config)
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for item in files:
        if features.get("enable_file_banner_check", True) and not item.has_file_banner:
            violations.append(_violation(item.file_key, "C文件缺少文件头文档注释", 0, 1))
        if item.is_header and features.get("enable_header_decl_doc_check", True):
            lines = Path(item.path).read_text(encoding="utf-8", errors="replace").splitlines()
            # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
            for name, line in undocumented_prototypes(lines):
                target = f"{item.file_key}::{name}@{line}"
                violations.append(_violation(target, "C头文件声明缺少前置文档注释", 0, 1))
    return violations


def _function_violations(
    functions: list[CFunctionMetrics],
    config: dict[str, Any],
) -> list[dict[str, str]]:
    """逐函数跑尺寸/循环/嵌套/递归/文档/行内复杂注释检查."""
    features = comment_features(config)
    thresholds = config["c_thresholds"]
    exclusions = config.get("c_exclusions", {})
    violations: list[dict[str, str]] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for func in functions:
        violations.extend(_one_function_violations(func, features, thresholds, exclusions))
    return violations


def _one_function_violations(
    func: CFunctionMetrics,
    features: dict[str, Any],
    thresholds: dict[str, Any],
    exclusions: dict[str, Any],
) -> list[dict[str, str]]:
    """单函数全部启用项；白名单不放行嵌套与行内复杂注释."""
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
    # 复杂语句（循环/同步/frexp 等）必须有贴身行内注释；L4 路径还要求 why 线索。
    if features.get("enable_inline_complex_check", False) and func.uncommented_complex > 0:
        issue = "C复杂语句缺少why行内注释" if features.get("enable_why_semantics", False) else "C复杂语句缺少行内注释"
        out.append(_violation(target, issue, func.uncommented_complex, 0))
    return out


def _loops_allowed(func: CFunctionMetrics, exclusions: dict[str, Any]) -> bool:
    """函数名白名单或路径 glob（如 ``kernel/**``）命中则允许必要单层循环."""
    if func.name in set(exclusions.get("loop_allowed_functions", [])):
        return True
    patterns = list(exclusions.get("loop_allowed_file_patterns", []))
    return any(fnmatch.fnmatch(func.file_key, pattern) for pattern in patterns)


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """统一违规记录字段，便于 CI 日志与后续 JSON 化."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


def main() -> int:
    """跑 C 门禁并打印紧凑结论；无 ``[c_scan]`` 时跳过（兼容旧配置）."""
    config = load_config()
    if "c_scan" not in config:
        print("[INFO] quality-gate.toml 无 [c_scan]，跳过 C 门禁")
        return 0
    files, functions = measure_c_files(
        list(config["c_scan"]["include_paths"]),
        list(config.get("c_exclusions", {}).get("file_patterns", [])),
        why_file_patterns=why_include_patterns(config),
    )
    violations = validate_c(files, functions, config)
    print(f"[INFO] C 扫描文件 {len(files)}，函数 {len(functions)}，违规 {len(violations)}")
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']} {item['current']}>{item['limit']}")
    if violations:
        print("❌ [C-QUALITY-GATE-FAIL] C/CUDA 结构度量未通过")
        return 1
    print("✅ [C-QUALITY-GATE-PASS] C/CUDA 结构度量通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
