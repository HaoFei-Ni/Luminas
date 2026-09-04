"""Lightweight C cyclomatic complexity and ``if`` nesting depth (regex spans).

McCabe-style decision points: ``if`` / ``for`` / ``while`` / ``case`` / ``&&`` /
``||`` / ternary ``?``. Nesting counts brace-scoped ``if`` depth (eng-skill ≤2).
"""

from __future__ import annotations

import re

from tools.checks.native.complexity_nest import NestScan, nest_step
from tools.checks.native.complexity_strip import strip_comments_and_strings

_DECISION = re.compile(r"\b(?:if|for|while|case)\b|&&|\|\||\?")


def measure_c_complexity(body_lines: list[str]) -> tuple[int, int]:
    """Return ``(cyclomatic, max_if_nesting)`` for a function body."""
    text = strip_comments_and_strings("\n".join(body_lines))
    cyclomatic = 1 + len(_DECISION.findall(text))
    return cyclomatic, _max_if_nesting(text)


def _max_if_nesting(text: str) -> int:
    """Max nested ``if`` depth; sequential ``if`` at one scope stays depth 1."""
    state = NestScan()
    i = 0
    n = len(text)
    # 必须单遍：``if`` 只提高 pending；进入 ``{`` 才把嵌套压入作用域。
    while i < n:
        i = nest_step(state, text, i)
    return state.max_nest
