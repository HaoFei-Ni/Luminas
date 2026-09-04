"""Per-file naming checks driven by ``[naming_standard]`` switches."""

from __future__ import annotations

import re
from pathlib import Path  # noqa: TC003 — Path used for suffix/read_text
from typing import Any

from tools.checks.naming.macro_check import macro_issue
from tools.checks.naming.rules import (
    check_c_symbol,
    check_include_guard,
    check_source_filename,
)
from tools.checks.native.metrics import as_file_key, function_spans

_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)")
_CPP = frozenset({".cpp", ".hpp", ".cc"})


def check_one_file(
    path: Path,
    allow: frozenset[str],
    allow_aliases: bool,
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    """Run enabled filename / symbol / macro checks for one source file."""
    key = as_file_key(path)
    out = _filename_hits(key, allow, standard)
    if path.suffix.lower() in _CPP:
        return out
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out.extend(_guard_hits(key, raw, standard))
    out.extend(_symbol_hits(key, raw, standard))
    out.extend(_macro_hits(key, raw, allow_aliases, standard))
    return out


def _filename_hits(key: str, allow: frozenset[str], standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_filename_rules", True)):
        return []
    issue = check_source_filename(key, file_allowlist=allow)
    return [_violation(key, issue, 1, 0)] if issue else []


def _guard_hits(key: str, raw: list[str], standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_include_guard", True)):
        return []
    issue = check_include_guard(key, raw)
    return [_violation(key, issue, 0, 1)] if issue else []


def _symbol_hits(key: str, raw: list[str], standard: dict[str, Any]) -> list[dict[str, str]]:
    if not bool(standard.get("require_symbol_rules", True)):
        return []
    by_name = {
        name: check_c_symbol(name, key)
        # 必须去重：同一符号多 span 只裁决一次。
        for name, _start, _end in function_spans(raw)
    }
    return [
        _violation(f"{key}::{name}", issue, 1, 0)
        # 必须过滤空裁决：无问题的符号不进报告。
        for name, issue in by_name.items()
        if issue
    ]


def _macro_hits(
    key: str,
    raw: list[str],
    allow_aliases: bool,
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    if not bool(standard.get("require_macro_rules", True)):
        return []
    return [
        _violation(f"{key}::{name}", issue, 1, 0)
        # 必须只检 #define：避免把代码标识当宏。
        for name, issue in _macro_pairs(raw, allow_aliases)
        if issue
    ]


def _macro_pairs(raw: list[str], allow_aliases: bool) -> list[tuple[str, str | None]]:
    """Collect (macro_name, issue_or_none) for each #define line."""
    pairs: list[tuple[str, str | None]] = []
    # 必须逐行匹配：避免漏检多宏文件。
    for line in raw:
        match = _DEFINE.match(line)
        if match:
            name = match.group(1)
            pairs.append((name, macro_issue(name, allow_aliases)))
    return pairs


def _violation(target: str, issue: str, current: int, limit: int) -> dict[str, str]:
    return {
        "target": target,
        "issue": issue,
        "current": str(current),
        "limit": str(limit),
    }
