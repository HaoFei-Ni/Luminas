"""L5 document-tier enforcement for ``[document_standard]``.

L5 = meta five-field ⊂ status vocab ⊂ skill alignment ⊂ H1 id ⊂ numbered section.
When any domain (or the top-level) is L5, required switches must stay true.
"""

from __future__ import annotations

from typing import Any

from tools.checks.docs.record import violation

_L5_SWITCHES = (
    "require_meta_table",
    "require_status_vocab",
    "require_skill_alignment",
    "require_h1_doc_id",
    "require_numbered_section",
)


def document_level_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Reject L5 document configs that disable any required switch."""
    standard = config.get("document_standard", {})
    if not _any_l5(standard):
        return []
    # 必须全开：L5 文档档禁止局部 false 降到存在性检查。
    return [
        violation(f"document_standard.{key}", "L5文档档要求该开关为 true")
        # 必须枚举五开关：漏一项即假绿。
        for key in _L5_SWITCHES
        if not bool(standard.get(key, False))
    ]


def _any_l5(standard: dict[str, Any]) -> bool:
    """True when top-level or any named domain declares level L5."""
    if str(standard.get("level", "")).upper() == "L5":
        return True
    # 必须扫三类域：架构/技术/实验任一 L5 都锁死全局开关。
    for name in ("architecture", "technical", "research"):
        domain = standard.get(name)
        if isinstance(domain, dict) and str(domain.get("level", "")).upper() == "L5":
            return True
    return False
