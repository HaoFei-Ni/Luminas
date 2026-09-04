"""Prototype-window parsing for C header doc-comment checks."""

from __future__ import annotations

import re

_FUNC_PROTO = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*;"
)
_CONTROL = frozenset({"if", "for", "while", "switch", "do", "return"})


def prototype_at(lines: list[str], start: int) -> tuple[str | None, int | None]:
    """若 ``start`` 起是 ``name(...);`` 原型，返回名字与结束行下标."""
    window: list[str] = []
    # 必须窗口扫描：花括号出现即非原型，分号闭合后再解析名字。
    for index in range(start, min(start + 12, len(lines))):
        window.append(lines[index].rstrip())
        joined = " ".join(part.strip() for part in window)
        done, name = proto_step(joined)
        if not done:
            continue
        return proto_window_result(name, index)
    return None, None


def proto_step(joined: str) -> tuple[bool, str | None]:
    """Return (done, name); done means stop widening the prototype window."""
    if "{" in joined:
        return True, None
    if ";" not in joined:
        return False, None
    return True, parse_proto_window(joined)


def parse_proto_window(joined: str) -> str | None:
    """Return prototype name from a joined window that already contains ``;``."""
    match = _FUNC_PROTO.search(joined)
    if match is None:
        return None
    name = match.group(1)
    return None if name in _CONTROL else name


def proto_window_result(name: str | None, index: int) -> tuple[str | None, int | None]:
    """Normalize a finished prototype window into ``(name, end_line)``."""
    if name is None:
        return None, None
    return name, index
