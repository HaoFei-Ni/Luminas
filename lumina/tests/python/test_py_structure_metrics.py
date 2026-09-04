"""Unit tests for McCabe / control-nesting structure metrics."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from tools import quality_metrics
from tools.py_structure_metrics import measure_function

if TYPE_CHECKING:
    from pathlib import Path


def test_simple_function_has_base_cyclomatic() -> None:
    """A straight-line function has cyclomatic complexity 1 and nest 0."""
    tree = ast.parse("def f():\n    return 1\n")
    metrics = measure_function(tree.body[0])
    assert metrics.cyclomatic == 1
    assert metrics.control_nesting == 0


def test_if_else_increments_cyclomatic_and_nesting() -> None:
    """Each decision adds CC; nested if raises control nesting."""
    source = "def f(x):\n    if x:\n        if x > 1:\n            return 1\n    return 0\n"
    metrics = measure_function(ast.parse(source).body[0])
    assert metrics.cyclomatic >= 3
    assert metrics.control_nesting >= 2


def test_measure_files_attaches_structure(tmp_path: Path) -> None:
    """quality_metrics.measure_files fills cyclomatic and control_nesting."""
    path = tmp_path / "sample.py"
    path.write_text("def g(n):\n    while n:\n        n -= 1\n    return n\n", encoding="utf-8")
    _, functions = quality_metrics.measure_files(
        [str(path)],
        count_blank_lines=False,
        count_comment_lines=False,
        exclude_patterns=[],
    )
    assert len(functions) == 1
    assert functions[0].cyclomatic is not None and functions[0].cyclomatic >= 2
    assert functions[0].control_nesting is not None and functions[0].control_nesting >= 1
