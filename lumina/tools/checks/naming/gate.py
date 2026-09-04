"""命名规范门禁（LUM-ENG-101 L5 文件命名质量）：文件名 + C/CUDA 符号.

由 ``quality-gate.toml`` ``[naming_standard]`` 驱动；经 ``run_quality_gate`` 调用。
"""

from __future__ import annotations

from typing import Any

from tools.checks.naming.file_check import check_one_file
from tools.checks.naming.level import naming_level_violations
from tools.checks.native.metrics import collect_c_files
from tools.support.gate_config import load_quality_gate as load_config


def naming_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Collect L5 naming violations for configured C/CUDA roots."""
    standard = config.get("naming_standard", {})
    if not standard.get("enable", False):
        return []
    out = naming_level_violations(config)
    roots = list(standard.get("include_paths") or config.get("c_scan", {}).get("include_paths", []))
    exclude = list(standard.get("file_patterns") or config.get("c_exclusions", {}).get("file_patterns", []))
    allow = frozenset(standard.get("file_allowlist", []))
    allow_aliases = bool(standard.get("allow_baseline_macro_aliases", True))
    files = collect_c_files(roots, exclude)
    # 单遍：逐文件隔离，避免跨文件状态污染命名裁决。
    for path in files:
        out.extend(check_one_file(path, allow, allow_aliases, standard))
    return out


def main() -> int:
    """Run naming gate and print a compact summary."""
    config = load_config()
    if "naming_standard" not in config or not config["naming_standard"].get("enable", False):
        print("[INFO] naming_standard 未启用，跳过命名门禁")
        return 0
    violations = naming_violations(config)
    print(f"[INFO] 命名扫描违规 {len(violations)}")
    # 单遍：逐条输出，避免汇总丢失定位信息。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print("[FAIL] naming-l5")
        return 1
    print("[PASS] naming-l5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
