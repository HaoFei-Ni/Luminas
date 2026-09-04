"""Unit tests for C-side complex-statement inline comment heuristics."""

from __future__ import annotations

from tools.checks.comments.comments import uncommented_complex_c_lines


def test_c_for_without_comment_is_flagged() -> None:
    """Bare for-loop must be reported as missing inline why-comment."""
    body = [
        "int f(void) {",
        "    for (i = 0; i < n; ++i)",
        "        x[i] = 0;",
        "}",
    ]
    assert uncommented_complex_c_lines(body) == [2]


def test_c_for_with_prev_comment_passes() -> None:
    """Comment on the previous line satisfies the adjacency rule (L0)."""
    body = [
        "int f(void) {",
        "    /* 单层扫描：有限性门禁。 */",
        "    for (i = 0; i < n; ++i)",
        "        x[i] = 0;",
        "}",
    ]
    assert uncommented_complex_c_lines(body) == []


def test_c_syncthreads_needs_comment() -> None:
    """CUDA barrier without why-comment is a complex unmarked site."""
    body = [
        "__global__ void k() {",
        "    __syncthreads();",
        "}",
    ]
    assert uncommented_complex_c_lines(body) == [2]


def test_c_for_inside_string_not_flagged() -> None:
    """String literal containing ``for`` must not count as a complex loop."""
    body = [
        "void f(void) {",
        '    throw std::runtime_error("too large for int32");',
        "}",
    ]
    assert uncommented_complex_c_lines(body, require_why=True) == []


def test_c_require_why_rejects_boilerplate_adjacent() -> None:
    """With require_why, adjacent what-only comment still counts as unmarked."""
    body = [
        "int f(void) {",
        "    /* 单层遍历：退出/边界见循环头。 */",
        "    for (i = 0; i < n; ++i)",
        "        x[i] = 0;",
        "}",
    ]
    assert uncommented_complex_c_lines(body) == []
    assert uncommented_complex_c_lines(body, require_why=True) == [3]
