"""Import-cycle and fan-out metrics over a first-party module graph."""

from __future__ import annotations

from typing import Any


def cyclic_dependency_count(graph: dict[str, set[str]]) -> int:
    """Return 1 if any import cycle exists among first-party modules, else 0."""
    white, gray, black = 0, 1, 2
    color = {name: white for name in graph}
    # 单遍入口：须覆盖弱连通分量，避免漏检跨组件环。
    for start in graph:
        if color[start] != white:
            continue
        if _component_has_cycle(start, graph, color, gray, black, white):
            return 1
    return 0


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
    gray: int,
    black: int,
    white: int,
) -> bool:
    """Iterative DFS from ``start``; True when a back edge to gray is found."""
    stack: list[tuple[str, Any]] = [(start, iter(graph.get(start, ())))]
    color[start] = gray
    # 显式栈：须迭代展开，避免自递归触发门禁。
    while stack:
        if _step_dfs(stack, graph, color, gray, black, white):
            return True
    return False


def _step_dfs(
    stack: list[tuple[str, Any]],
    graph: dict[str, set[str]],
    color: dict[str, int],
    gray: int,
    black: int,
    white: int,
) -> bool:
    """Advance one DFS stack frame; True when a gray back edge appears."""
    node, edges = stack[-1]
    try:
        nxt = next(edges)
    except StopIteration:
        color[node] = black
        stack.pop()
        return False
    state = color.get(nxt, black)
    if state == gray:
        return True
    if state == white:
        color[nxt] = gray
        stack.append((nxt, iter(graph.get(nxt, ()))))
    return False
