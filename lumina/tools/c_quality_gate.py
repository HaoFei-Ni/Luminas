"""C/C++/CUDA 结构门禁入口：尺寸 + 循环 + 递归 + 注释策略.

注释策略真值源：``quality-gate.toml`` 的 ``[comment_standard]``（接入本模块）。
``[c_features]`` 中的文档开关与之对齐；``require_inline_on_complex`` 检查复杂行行内注释。

本文件只编排阈值比对；测量逻辑在 ``c_quality_metrics``。
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

from tools.c_file_gate import doc_file_violations, file_structure_violations
from tools.c_function_gate import function_structure_violations
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
    """合并 ``[comment_standard]`` 到 C 文档/行内相关 feature 开关."""
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
    features = comment_features(config)
    violations: list[dict[str, str]] = []
    violations.extend(file_structure_violations(files, config))
    violations.extend(doc_file_violations(files, features))
    violations.extend(function_structure_violations(functions, config, features))
    return violations


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
