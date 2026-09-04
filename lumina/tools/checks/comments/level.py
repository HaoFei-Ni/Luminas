"""L5 comment-tier enforcement for ``[comment_standard]``.

L0 = adjacency exists · L4 = why markers · L5 = L4 + forced switches +
numeric-contract banners on product core paths.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any, Protocol

from tools.checks.comments.level_read import read_banner


class _BannerFile(Protocol):
    file_key: str
    path: str


_L5_SWITCHES = (
    "require_file_banner",
    "require_function_doc",
    "require_header_decl_doc",
    "require_inline_on_complex",
    "require_why_semantics",
)

_DEFAULT_MARKERS = (
    "L5",
    "2-ulp",
    "ulp",
    "bit-exact",
    "有限",
    "无损",
    "预言机",
    "LUMA_ULP",
)


def comment_level_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Reject L5 configs that disable any required comment switch."""
    standard = config.get("comment_standard", {})
    if str(standard.get("level", "")).upper() != "L5":
        return []
    # 必须全开：L5 注释档禁止用局部 false 降级到 L0。
    return [
        _violation(f"comment_standard.{key}", "L5注释档要求该开关为 true", 0, 1)
        # 必须枚举五开关：漏一项即假绿。
        for key in _L5_SWITCHES
        if not bool(standard.get(key, False))
    ]


def numeric_contract_banner_violations(
    files: list[Any],
    config: dict[str, Any],
) -> list[dict[str, str]]:
    """Require numeric-contract clues in banners of matched core product files."""
    standard = config.get("comment_standard", {})
    if not bool(standard.get("require_numeric_contract_banner", False)):
        return []
    patterns = list(standard.get("numeric_contract_file_patterns", []))
    if not patterns:
        return []
    markers = list(standard.get("numeric_contract_markers", list(_DEFAULT_MARKERS)))
    out: list[dict[str, str]] = []
    # 单遍：只检核心路径，避免把有损基线误绑 L5 契约。
    for item in files:
        violation = _contract_banner_violation(item, patterns, markers)
        if violation is not None:
            out.append(violation)
    return out


def _contract_banner_violation(
    item: _BannerFile,
    patterns: list[str],
    markers: list[str],
) -> dict[str, str] | None:
    """Return one banner violation when a matched file lacks contract clues."""
    if not _matched(item.file_key, patterns):
        return None
    if _has_marker(read_banner(Path(item.path)), markers):
        return None
    return _violation(
        item.file_key,
        "L5核心文件头缺少数值契约线索（L5/2-ulp/bit-exact/有限等）",
        0,
        1,
    )


def _matched(file_key: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(file_key, pat) for pat in patterns)


def _has_marker(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }
