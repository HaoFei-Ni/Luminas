"""Unit tests for C cyclomatic / if-nesting measurement."""

from __future__ import annotations

from tools.checks.native.complexity import measure_c_complexity


def test_cyclomatic_counts_if_and_logical() -> None:
    """``if`` and ``&&`` each add a decision point."""
    body = ["int f(int a, int b) {", "  if (a && b) return 1;", "  return 0;", "}"]
    cyclomatic, _nest = measure_c_complexity(body)
    assert cyclomatic >= 3


def test_if_nesting_two_levels() -> None:
    """Two nested ``if`` blocks report nesting depth 2."""
    body = [
        "int f(int a, int b) {",
        "  if (a) {",
        "    if (b) { return 1; }",
        "  }",
        "  return 0;",
        "}",
    ]
    _cc, nest = measure_c_complexity(body)
    assert nest == 2


def test_comments_do_not_count_as_if() -> None:
    """Commented ``if`` must not inflate cyclomatic complexity."""
    body = ["int f(void) {", "  /* if (x) */", "  return 0;", "}"]
    cyclomatic, nest = measure_c_complexity(body)
    assert cyclomatic == 1
    assert nest == 0
