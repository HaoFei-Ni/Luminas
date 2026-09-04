"""Parse leading Markdown meta tables for formal LUM-* docs."""

from __future__ import annotations

import re

_FIELD_ROW = re.compile(r"^\|\s*(?P<key>[^|]+?)\s*\|\s*(?P<val>[^|]*?)\s*\|")
_SKIP_KEYS = frozenset({"字段", ":---", ":---|:---"})


def parse_meta_fields(lines: list[str]) -> dict[str, str]:
    """Parse the leading ``| 字段 | 内容 |`` table into a flat map."""
    fields: dict[str, str] = {}
    # 单遍：只吃元信息表，避免正文表格污染字段。
    for line in lines:
        if line.startswith("##"):
            break
        pair = _row_pair(line)
        if pair is not None:
            fields[pair[0]] = pair[1]
    return fields


def _row_pair(line: str) -> tuple[str, str] | None:
    """Return (key, value) for a meta table row, else None."""
    if line.startswith("#"):
        return None
    match = _FIELD_ROW.match(line)
    if match is None:
        return None
    key = match.group("key").strip()
    if key in _SKIP_KEYS or key.startswith(":"):
        return None
    return key, match.group("val").strip()
