"""Unit tests for Python-side complex-statement inline comment heuristics."""

from __future__ import annotations

from tools.inline_comments import is_why_comment, uncommented_complex_py_lines


def test_python_for_with_hash_passes() -> None:
    """Python for-loop with trailing # comment is accepted at L0."""
    body = [
        "def f(xs):",
        "    for x in xs:  # 单遍归约",
        "        s += x",
    ]
    assert uncommented_complex_py_lines(body) == []


def test_python_for_without_comment_flagged() -> None:
    """Python for-loop without adjacent # must be flagged."""
    body = [
        "def f(xs):",
        "    for x in xs:",
        "        s += x",
    ]
    assert uncommented_complex_py_lines(body) == [2]


def test_is_why_comment_accepts_invariant_clue() -> None:
    """L4: comments with why clues (invariant / finite / sync) pass."""
    assert is_why_comment("单层扫描：有限性门禁。")
    assert is_why_comment("归约前必须看见全部局部 amax。")
    assert is_why_comment("frac ∈ [0.5,1)，binary exponent for ldexp restore")
    assert is_why_comment("avoid shared-buffer alias before store")


def test_is_why_comment_rejects_boilerplate_what() -> None:
    """L4: template / pure-what comments fail the why heuristic."""
    assert not is_why_comment("单层遍历：退出/边界见循环头与函数 docstring。")
    assert not is_why_comment("遍历数组")
    assert not is_why_comment("loop over items")
    assert not is_why_comment("单遍归约")
    assert not is_why_comment("")


def test_python_require_why_needs_clue() -> None:
    """With require_why, trailing # must carry a why clue."""
    weak = [
        "def f(xs):",
        "    for x in xs:  # 单层遍历",
        "        s += x",
    ]
    strong = [
        "def f(xs):",
        "    for x in xs:  # 单遍：避免重复读同一 token 边界",
        "        s += x",
    ]
    assert uncommented_complex_py_lines(weak, require_why=True) == [2]
    assert uncommented_complex_py_lines(strong, require_why=True) == []
