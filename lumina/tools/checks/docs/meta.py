"""Per-file Markdown meta / structure checks for formal LUM-* docs."""

from __future__ import annotations

import re
from pathlib import Path  # noqa: TC003 — used at runtime for read_text
from typing import Any

from tools.checks.docs.meta_parse import parse_meta_fields
from tools.checks.docs.record import violation

_H1 = re.compile(r"^#\s+(?P<title>.+)$")
_SECTION = re.compile(r"^##\s+\d+")
_META_KEYS = ("状态", "版本", "日期", "权威技能", "关联文档")


def file_doc_violations(
    path: Path,
    file_key: str,
    domain: dict[str, Any],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    """Emit violations for one formal Markdown document."""
    lines = path.read_text(encoding="utf-8").splitlines()
    fields = parse_meta_fields(lines)
    out: list[dict[str, str]] = []
    out.extend(_meta_table_hits(file_key, fields, standard))
    out.extend(_status_hits(file_key, fields, standard))
    out.extend(_skill_hits(file_key, fields, domain, standard))
    out.extend(_h1_hits(file_key, lines, domain, standard))
    out.extend(_section_hits(file_key, lines, standard))
    return out


def _meta_table_hits(
    file_key: str,
    fields: dict[str, str],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    if not bool(standard.get("require_meta_table", False)):
        return []
    missing = [key for key in _META_KEYS if not fields.get(key)]
    if not missing:
        return []
    return [violation(file_key, f"文档元信息缺字段: {', '.join(missing)}")]


def _status_hits(
    file_key: str,
    fields: dict[str, str],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    if not bool(standard.get("require_status_vocab", False)):
        return []
    status = fields.get("状态", "")
    vocab = list(standard.get("status_vocab", ["生效", "草案", "计划"]))
    # 允许「生效（最小契约）」等后缀，只校验前缀用语。
    if any(status.startswith(word) for word in vocab):
        return []
    return [violation(file_key, f"文档状态用语非法（须以 {'/'.join(vocab)} 开头）")]


def _skill_hits(
    file_key: str,
    fields: dict[str, str],
    domain: dict[str, Any],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    if not bool(standard.get("require_skill_alignment", False)):
        return []
    required = str(domain.get("required_skill", ""))
    if required and required in fields.get("权威技能", ""):
        return []
    return [violation(file_key, f"权威技能未对齐域技能 {required}")]


def _h1_hits(
    file_key: str,
    lines: list[str],
    domain: dict[str, Any],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    if not bool(standard.get("require_h1_doc_id", False)):
        return []
    prefix = str(domain.get("doc_id_prefix", ""))
    title = _first_h1(lines)
    if prefix and prefix in title:
        return []
    return [violation(file_key, f"H1 缺少文档编号前缀 {prefix}")]


def _first_h1(lines: list[str]) -> str:
    """Return first H1 title text or empty string."""
    # 必须只取首个 H1：后续标题会污染编号前缀裁决。
    for line in lines:
        match = _H1.match(line)
        if match:
            return match.group("title")
    return ""


def _section_hits(
    file_key: str,
    lines: list[str],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    if not bool(standard.get("require_numbered_section", False)):
        return []
    if any(_SECTION.match(line) for line in lines):
        return []
    return [violation(file_key, "缺少编号章节（## N. …）")]
