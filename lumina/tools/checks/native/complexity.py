"""Lightweight C cyclomatic complexity and ``if`` nesting depth (regex spans).

McCabe-style decision points: ``if`` / ``for`` / ``while`` / ``case`` / ``&&`` /
``||`` / ternary ``?``. Nesting counts brace-scoped ``if`` depth (eng-skill ≤2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_DECISION = re.compile(r"\b(?:if|for|while|case)\b|&&|\|\||\?")


def measure_c_complexity(body_lines: list[str]) -> tuple[int, int]:
    """Return ``(cyclomatic, max_if_nesting)`` for a function body."""
    text = _strip_comments_and_strings("\n".join(body_lines))
    cyclomatic = 1 + len(_DECISION.findall(text))
    return cyclomatic, _max_if_nesting(text)


@dataclass
class _NestScan:
    """Mutable brace / pending-if state for one nesting pass."""

    brace: int = 0
    nest_at_brace: list[int] = field(default_factory=lambda: [0])
    pending_if: int = 0
    max_nest: int = 0


def _max_if_nesting(text: str) -> int:
    """Max nested ``if`` depth; sequential ``if`` at one scope stays depth 1."""
    state = _NestScan()
    i = 0
    n = len(text)
    # 必须单遍：``if`` 只提高 pending；进入 ``{`` 才把嵌套压入作用域。
    while i < n:
        i = _nest_step(state, text, i)
    return state.max_nest


def _nest_step(state: _NestScan, text: str, index: int) -> int:
    """Advance nesting scan by one token or character."""
    if text.startswith("if", index) and _keyword_boundary(text, index, 2):
        state.pending_if = state.nest_at_brace[state.brace] + 1
        state.max_nest = max(state.max_nest, state.pending_if)
        return index + 2
    ch = text[index]
    if ch == "{":
        state.brace += 1
        entered = state.pending_if if state.pending_if > 0 else state.nest_at_brace[state.brace - 1]
        state.nest_at_brace.append(entered)
        state.pending_if = 0
        return index + 1
    if ch == "}":
        if state.brace > 0:
            state.nest_at_brace.pop()
            state.brace -= 1
        state.pending_if = 0
        return index + 1
    return index + 1


def _keyword_boundary(text: str, index: int, length: int) -> bool:
    """True when ``text[index:index+length]`` is a C keyword token."""
    end = index + length
    if end > len(text):
        return False
    before_ok = index == 0 or not (text[index - 1].isalnum() or text[index - 1] == "_")
    after_ok = end == len(text) or not (text[end].isalnum() or text[end] == "_")
    return before_ok and after_ok


def _strip_comments_and_strings(source: str) -> str:
    """Remove // and /* */ comments and quoted strings to avoid false keywords."""
    out: list[str] = []
    i = 0
    n = len(source)
    # 必须状态机剥离：注释/字符串内的 if 不得计入复杂度。
    while i < n:
        if source.startswith("//", i):
            i = _skip_line(source, i)
            out.append("\n")
            continue
        if source.startswith("/*", i):
            i = _skip_block_comment(source, i)
            continue
        if source[i] in {'"', "'"}:
            i = _skip_string(source, i, source[i])
            out.append('""')
            continue
        out.append(source[i])
        i += 1
    return "".join(out)


def _skip_line(source: str, index: int) -> int:
    end = source.find("\n", index)
    return len(source) if end < 0 else end + 1


def _skip_block_comment(source: str, index: int) -> int:
    end = source.find("*/", index + 2)
    return len(source) if end < 0 else end + 2


def _skip_string(source: str, index: int, quote: str) -> int:
    i = index + 1
    n = len(source)
    # 必须处理转义：避免 \" 提前结束字符串扫描。
    while i < n:
        if source[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if source[i] == quote:
            return i + 1
        i += 1
    return n
