"""Clone-block and duplication-ratio metrics for the architecture gate."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_WINDOW = 6
_MIN_CLONE_LOCS = 2


def duplication_stats(files: list[tuple[str, Path]]) -> tuple[int, int]:
    """Return (duplicate block groups, ceil duplication ratio percent)."""
    windows: dict[str, list[tuple[str, int]]] = defaultdict(list)
    total_lines = 0
    # 单遍文件：须先计量有效行再哈希，避免空文件除零。
    for file_key, path in files:
        lines = _significant_lines(path.read_text(encoding="utf-8").splitlines())
        total_lines += len(lines)
        _index_windows(file_key, lines, windows)
    block_groups, dup_starts = _clone_groups(windows)
    dup_lines = min(total_lines, len(dup_starts) * _WINDOW)
    ratio = 0 if total_lines == 0 else math.ceil(100.0 * dup_lines / total_lines)
    return block_groups, ratio


def _clone_groups(
    windows: dict[str, list[tuple[str, int]]],
) -> tuple[int, set[tuple[str, int]]]:
    """Count hash buckets with ≥2 locs and collect their starts."""
    block_groups = 0
    dup_starts: set[tuple[str, int]] = set()
    # 单遍哈希桶：出现 ≥2 次才计组，避免把独有瓦片当成克隆。
    for locs in windows.values():
        if len(locs) < _MIN_CLONE_LOCS:
            continue
        block_groups += 1
        dup_starts.update(locs)
    return block_groups, dup_starts


def _significant_lines(raw: list[str]) -> list[str]:
    """Strip blanks and full-line comments for clone detection."""
    out: list[str] = []
    # 单遍过滤：须去掉注释/空行，避免假克隆抬高重复率。
    for line in raw:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append(stripped)
    return out


def _index_windows(file_key: str, lines: list[str], windows: dict[str, list[tuple[str, int]]]) -> None:
    """Hash every non-overlapping ``_WINDOW``-line tile and record its start."""
    if len(lines) < _WINDOW:
        return
    # 非重叠瓦片：须固定步长，避免滑窗把同一克隆计成多组。
    for start in range(0, len(lines) - _WINDOW + 1, _WINDOW):
        chunk = "\n".join(lines[start : start + _WINDOW])
        digest = hashlib.sha1(chunk.encode("utf-8"), usedforsecurity=False).hexdigest()
        windows[digest].append((file_key, start))
