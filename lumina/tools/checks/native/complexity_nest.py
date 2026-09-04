"""``if`` nesting scan helpers for C complexity measurement."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NestScan:
    """Mutable brace / pending-if state for one nesting pass."""

    brace: int = 0
    nest_at_brace: list[int] = field(default_factory=lambda: [0])
    pending_if: int = 0
    max_nest: int = 0


def nest_step(state: NestScan, text: str, index: int) -> int:
    """Advance nesting scan by one token or character."""
    if text.startswith("if", index) and keyword_boundary(text, index, 2):
        return _nest_if_token(state, index)
    ch = text[index]
    if ch == "{":
        return _nest_open_brace(state, index)
    if ch == "}":
        return _nest_close_brace(state, index)
    return index + 1


def keyword_boundary(text: str, index: int, length: int) -> bool:
    """True when ``text[index:index+length]`` is a C keyword token."""
    end = index + length
    if end > len(text):
        return False
    return _ident_boundary_ok(text, index, end)


def _nest_if_token(state: NestScan, index: int) -> int:
    """Record pending ``if`` depth before the next ``{`` enters scope."""
    state.pending_if = state.nest_at_brace[state.brace] + 1
    state.max_nest = max(state.max_nest, state.pending_if)
    return index + 2


def _nest_open_brace(state: NestScan, index: int) -> int:
    """Push brace scope and commit pending ``if`` nesting."""
    state.brace += 1
    entered = state.pending_if if state.pending_if > 0 else state.nest_at_brace[state.brace - 1]
    state.nest_at_brace.append(entered)
    state.pending_if = 0
    return index + 1


def _nest_close_brace(state: NestScan, index: int) -> int:
    """Pop brace scope and discard pending ``if``."""
    if state.brace > 0:
        state.nest_at_brace.pop()
        state.brace -= 1
    state.pending_if = 0
    return index + 1


def _ident_boundary_ok(text: str, index: int, end: int) -> bool:
    """True when token boundaries are not alphanumeric/underscore."""
    before_ok = index == 0 or not _is_ident_char(text[index - 1])
    after_ok = end == len(text) or not _is_ident_char(text[end])
    return before_ok and after_ok


def _is_ident_char(char: str) -> bool:
    """C identifier continuation character."""
    return char.isalnum() or char == "_"
