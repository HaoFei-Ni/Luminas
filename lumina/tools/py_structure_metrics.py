"""Python 函数结构度量：圈复杂度（McCabe）与控制块最大嵌套深度.

从历史 ``audit_complexity`` 收敛而来；阈值在 ``quality-gate.toml``，本模块只测量。
认知复杂度仍由 complexipy 提供，二者互补（人脑负担 vs 路径数）。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class StructureMetrics:
    """Cyclomatic complexity and peak control-block nesting for one function."""

    cyclomatic: int
    control_nesting: int


_DECISION = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)
_NEST_ONLY = (ast.With, ast.AsyncWith, ast.Try)


class _StructureVisitor(ast.NodeVisitor):
    """Accumulate McCabe CC and control nesting inside one function body."""

    def __init__(self) -> None:
        self.cyclomatic = 1
        self.max_depth = 0
        self._depth = 0

    def visit(self, node: ast.AST) -> None:
        """Dispatch decision / nest nodes; BoolOp and IfExp add CC without nesting."""
        if isinstance(node, _DECISION):
            self.cyclomatic += 1
            self._enter(node)
            return
        if isinstance(node, _NEST_ONLY):
            self._enter(node)
            return
        if isinstance(node, ast.IfExp):
            self.cyclomatic += 1
            self.generic_visit(node)
            return
        if isinstance(node, ast.BoolOp):
            self.cyclomatic += len(node.values) - 1
            self.generic_visit(node)
            return
        self.generic_visit(node)

    def _enter(self, node: ast.AST) -> None:
        self._depth += 1
        self.max_depth = max(self.max_depth, self._depth)
        self.generic_visit(node)
        self._depth -= 1


def measure_function(node: ast.AST) -> StructureMetrics:
    """Return structure metrics for a ``FunctionDef`` / ``AsyncFunctionDef`` node."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise TypeError(f"expected function def, got {type(node).__name__}")
    visitor = _StructureVisitor()
    visitor.visit(node)
    return StructureMetrics(cyclomatic=visitor.cyclomatic, control_nesting=visitor.max_depth)
