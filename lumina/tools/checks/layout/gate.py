"""目录结构质量门禁（LUM-ARC-101 物理三层 + 内容平面）.

真值源：``quality-gate.toml`` ``[layout_standard]``；经 ``run_quality_gate`` 调用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.checks.layout.level import layout_level_violations
from tools.checks.layout.tree import ascii_dir_hits, banned_root_hits, missing_path_hits
from tools.support.gate_config import load_quality_gate as load_config

_LUMINA = Path(__file__).resolve().parents[3]


def layout_violations(config: dict[str, Any], *, root: Path | None = None) -> list[dict[str, str]]:
    """Collect L5 directory-structure violations under ``lumina/``."""
    standard = config.get("layout_standard", {})
    if not standard.get("enable", False):
        return []
    base = root or _LUMINA
    out = layout_level_violations(config)
    out.extend(_product_hits(base, standard))
    out.extend(_plane_hits(base, standard))
    out.extend(_docs_hits(base, standard))
    out.extend(_banned_hits(base, standard))
    out.extend(_ascii_hits(base, standard))
    return out


def _product_hits(base: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_product_layers", False)):
        return []
    layers = list(standard.get("product_layers", ["algorithm", "kernel", "wrapper"]))
    return missing_path_hits(base, layers, "缺少产品物理层目录（algorithm/kernel/wrapper）")


def _plane_hits(base: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_content_planes", False)):
        return []
    planes = list(
        standard.get(
            "content_planes",
            ["tools", "tests", "docs", "theory", "research", "experiments", "refs"],
        )
    )
    return missing_path_hits(base, planes, "缺少内容平面目录（LUM-ARC-001 §4.1）")


def _docs_hits(base: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_docs_domains", False)):
        return []
    domains = list(standard.get("docs_domains", ["docs/arc", "docs/eng", "docs/res", "docs/pm"]))
    return missing_path_hits(base, domains, "缺少文档域目录（arc/eng/res/pm）")


def _banned_hits(base: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("forbid_banned_roots", False)):
        return []
    return banned_root_hits(base, list(standard.get("banned_roots", ["common", "include", "src", "lib"])))


def _ascii_hits(base: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_ascii_dir_names", False)):
        return []
    scan = list(standard.get("ascii_scan_roots", ["algorithm", "kernel", "wrapper", "docs"]))
    ignore = frozenset(standard.get("ascii_ignore_dir_names", [".cache", ".venv", "__pycache__"]))
    return ascii_dir_hits(base, scan, ignore)


def main() -> int:
    """CLI entry for the layout-quality stage."""
    config = load_config()
    standard = config.get("layout_standard", {})
    if not standard.get("enable", False):
        print("[INFO] layout_standard 未启用，跳过目录结构门禁")
        return 0
    violations = layout_violations(config)
    print(f"[INFO] layout-l5 findings={len(violations)}")
    # 单遍：逐条输出，避免汇总丢失定位。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print("[FAIL] layout-l5")
        return 1
    print("[PASS] layout-l5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
