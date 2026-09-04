"""File banner text extraction for L5 comment-tier checks."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_BANNER_END = re.compile(r"\*/")


def read_banner(path: Path) -> str:
    """Return leading file banner text (block or line comments)."""
    text = safe_text(path).lstrip("\ufeff").lstrip()
    if text.startswith("/*"):
        match = _BANNER_END.search(text)
        return text[: match.end()] if match else text[:800]
    if text.startswith("//"):
        return line_banner(text)
    return ""


def safe_text(path: Path) -> str:
    """Read file text, returning empty string on I/O failure."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def line_banner(text: str) -> str:
    """Collect consecutive leading ``//`` lines as one banner block."""
    chunk: list[str] = []
    # 必须连续 //：空行结束文件头注释块。
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        chunk.append(line)
    return "\n".join(chunk)
