"""Inline trailing-comment extraction for complex-line scans."""

from __future__ import annotations


def inline_comment_text(raw: str, c_style: bool) -> str | None:
    """Extract trailing comment on a code line, if any."""
    return _c_inline_comment(raw) if c_style else _python_inline_comment(raw)


def line_is_trivial(stripped: str, c_style: bool) -> bool:
    """True when the line cannot require an adjacent complex-line comment."""
    if not stripped or stripped in {"{", "}", "};"}:
        return True
    return is_comment_only(stripped, c_style) or (c_style and stripped.startswith("#"))


def is_comment_only(stripped: str, c_style: bool) -> bool:
    """True when the whole stripped line is a comment."""
    if not c_style:
        return stripped.startswith("#")
    return stripped == "*/" or stripped.startswith(("//", "/*", "*"))


def _python_inline_comment(raw: str) -> str | None:
    if "#" not in raw:
        return None
    if not raw[: raw.index("#")].strip():
        return None
    return raw[raw.index("#") :]


def _c_inline_comment(raw: str) -> str | None:
    if "//" in raw:
        return raw[raw.index("//") :]
    if "/*" not in raw:
        return None
    start = raw.index("/*")
    end = raw.find("*/", start)
    return raw[start : end + 2] if end >= 0 else None
