"""Generic CLI stage runner for L5 ``*_standard`` gates."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003 — used in public signatures
from typing import Any


def run_standard_stage(
    *,
    section: str,
    stage: str,
    load_config: Callable[[], dict[str, Any]],
    collect: Callable[[dict[str, Any]], list[dict[str, str]]],
) -> int:
    """Load config, collect findings, print summary, return process status."""
    config = load_config()
    standard = config.get(section, {})
    if not standard.get("enable", False):
        print(f"[INFO] {section} 未启用，跳过 {stage}")
        return 0
    violations = collect(config)
    print(f"[INFO] {stage} findings={len(violations)}")
    # 单遍：逐条输出，避免汇总丢失定位。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print(f"[FAIL] {stage}")
        return 1
    print(f"[PASS] {stage}")
    return 0
