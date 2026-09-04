"""命名规范门禁（LUM-ENG-101 L4）：文件名 + C/CUDA 符号.

由 ``quality-gate.toml`` ``[naming_standard]`` 驱动；经 ``run_quality_gate`` 调用。
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Any

from tools.c_quality_metrics import as_file_key, collect_c_files, function_spans
from tools.naming_rules import check_c_symbol, check_source_filename

_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)")


def load_config(config_path: str = "quality-gate.toml") -> dict[str, Any]:
    """Load quality-gate.toml from the lumina working directory."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with path.open("rb") as handle:
        return dict(tomllib.load(handle))


def naming_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Collect naming L4 violations for configured C/CUDA roots."""
    standard = config.get("naming_standard", {})
    if not standard.get("enable", False):
        return []
    roots = list(standard.get("include_paths") or config.get("c_scan", {}).get("include_paths", []))
    exclude = list(standard.get("file_patterns") or config.get("c_exclusions", {}).get("file_patterns", []))
    allow = frozenset(standard.get("file_allowlist", []))
    allow_aliases = bool(standard.get("allow_baseline_macro_aliases", True))
    files = collect_c_files(roots, exclude)
    out: list[dict[str, str]] = []
    # 单遍：逐文件隔离，避免跨文件状态污染命名裁决。
    for path in files:
        out.extend(_check_file(path, allow, allow_aliases))
    return out


def _check_file(path: Path, allow: frozenset[str], allow_aliases: bool) -> list[dict[str, str]]:
    """Run filename + symbol + macro checks for one source file."""
    key = as_file_key(path)
    out: list[dict[str, str]] = []
    file_issue = check_source_filename(key, file_allowlist=allow)
    if file_issue:
        out.append(_violation(key, file_issue, 1, 0))
    if path.suffix.lower() in {".cpp", ".hpp", ".cc"}:
        return out
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    seen: set[str] = set()
    # 单遍：只扫函数定义 span，避免把宏/类型当符号。
    for name, _start, _end in function_spans(raw):
        if name in seen:
            continue
        seen.add(name)
        issue = check_c_symbol(name, key)
        if issue:
            out.append(_violation(f"{key}::{name}", issue, 1, 0))
    out.extend(_macro_violations(key, raw, allow_aliases))
    return out


def _macro_violations(file_key: str, lines: list[str], allow_aliases: bool) -> list[dict[str, str]]:
    """Flag public-looking macros that are not LUMA_* (L4)."""
    out: list[dict[str, str]] = []
    # 单遍：只检 #define 名，避免把代码标识当宏。
    for line in lines:
        match = _DEFINE.match(line)
        if not match:
            continue
        name = match.group(1)
        if name.startswith("LUMA_"):
            if (not allow_aliases) and "BASELINE" in name:
                out.append(_violation(f"{file_key}::{name}", "禁止 LUMA_BASELINE_* 兼容别名", 1, 0))
            continue
        if name.endswith("_H") or name.endswith("_HPP"):
            continue  # include guard
        if name.startswith("_"):
            continue
        out.append(_violation(f"{file_key}::{name}", f"宏须 LUMA_ 前缀: {name}", 1, 0))
    return out


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    """Normalized violation record."""
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }


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
        print("❌ [NAMING-GATE-FAIL] 命名规范未通过")
        return 1
    print("✅ [NAMING-GATE-PASS] 命名规范通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
