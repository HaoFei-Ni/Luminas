"""Import-cycle and fan-out metrics over a first-party module graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class _DfsPalette:
    """Color codes for iterative import-cycle DFS."""

    white: int = 0
    gray: int = 1
    black: int = 2


def cyclic_dependency_count(graph: dict[str, set[str]]) -> int:
    """Return 1 if any import cycle exists among first-party modules, else 0."""
    palette = _DfsPalette()
    color = {name: palette.white for name in graph}
    # 单遍入口：须覆盖弱连通分量，避免漏检跨组件环。
    for start in graph:
        if _uncolored_component_has_cycle(start, graph, color, palette):
            return 1
    return 0


def _uncolored_component_has_cycle(
    start: str,
    graph: dict[str, set[str]],
    color: dict[str, int],
    palette: _DfsPalette,
) -> bool:
    """Run cycle detection from ``start`` only when it is still unvisited."""
    if color[start] != palette.white:
        return False
    return _component_has_cycle(start, graph, color, palette)


def max_fan_out(graph: dict[str, set[str]]) -> tuple[int, str]:
    """Return (max fan-out, module name achieving it)."""
    if not graph:
        return 0, ""
    best = max(graph.items(), key=lambda item: len(item[1]))
    return len(best[1]), best[0]


def _component_has_cycle(
    start: str,
    graph: dict[str, set[str]],
    color: dict[str, int],
    palette: _DfsPalette,
) -> bool:
    """Iterative DFS from ``start``; True when a back edge to gray is found."""
    stack: list[tuple[str, Any]] = [(start, iter(graph.get(start, ())))]
    color[start] = palette.gray
    # 显式栈：须迭代展开，避免自递归触发门禁。
    while stack:
        if _step_dfs(stack, graph, color, palette):
            return True
    return False


def _step_dfs(
    stack: list[tuple[str, Any]],
    graph: dict[str, set[str]],
    color: dict[str, int],
    palette: _DfsPalette,
) -> bool:
    """Advance one DFS stack frame; True when a gray back edge appears."""
    node, edges = stack[-1]
    try:
        nxt = next(edges)
    except StopIteration:
        color[node] = palette.black
        stack.pop()
        return False
    state = color.get(nxt, palette.black)
    if state == palette.gray:
        return True
    if state == palette.white:
        color[nxt] = palette.gray
        stack.append((nxt, iter(graph.get(nxt, ()))))
    return False
