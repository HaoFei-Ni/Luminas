"""Self-recursion detector for C/CUDA function bodies."""

from __future__ import annotations

import re

_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def has_self_recursion(func_name: str, body_lines: list[str]) -> bool:
    """Return True when ``func_name`` appears as a call inside its own body.

    Skips the defining header (text before the first ``{``) so the signature
    itself is not treated as a recursive call.
    """
    text = _strip_comments_and_strings("\n".join(body_lines))
    brace = text.find("{")
    if brace < 0:
        return False
    return any(match.group(1) == func_name for match in _CALL.finditer(text, brace + 1))


def _strip_comments_and_strings(text: str) -> str:
    """Drop // comments and rough string/char literals before call scanning."""
    lines: list[str] = []
    for line in text.splitlines():
        if "//" in line:
            line = line[: line.index("//")]
        lines.append(re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", '""', line))
    return "\n".join(lines)
