"""L1 / L2: pure-Python quality_metrics unit and property tests.

本文件不依赖 ``_luma_*`` 扩展，保证 ``uv run pytest`` 在未构建原生模块时
仍能 exit 0（避免「全 skip → exit 5」）。覆盖 schema 兼容层、行数口径、排除规则。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, strategies as st

from tools import quality_metrics


@pytest.mark.l1
def test_as_file_key_normalizes_separators() -> None:
    """Path keys must be POSIX-style so Windows and Unix reports compare equal."""
    assert quality_metrics.as_file_key(r"tests\python\a.py") == "tests/python/a.py"
    assert quality_metrics.as_file_key(Path("tests/python/a.py")) == "tests/python/a.py"


@pytest.mark.l1
def test_complexity_map_flat_schema_v8() -> None:
    """complexipy 8+ flat records normalize to (file_key, name) → complexity."""
    raw = [
        {
            "path": r"tests\python\a.py",
            "function_name": "foo",
            "complexity": 3,
            "file_name": "a.py",
        },
        {
            "path": "tests/python/b.py",
            "function_name": "bar",
            "complexity": 1,
            "file_name": "b.py",
        },
    ]
    assert quality_metrics.complexity_map(raw) == {
        ("tests/python/a.py", "foo"): 3,
        ("tests/python/b.py", "bar"): 1,
    }


@pytest.mark.l1
def test_complexity_map_group_schema_pre8() -> None:
    """Pre-8 grouped records flatten into the same lookup shape."""
    raw: list[dict[str, Any]] = [
        {
            "file_path": "theory/verify.py",
            "file_lines": 40,
            "functions": [
                {"function_name": "main", "cognitive_complexity": 2, "function_lines": 10},
                {"function_name": "helper", "cognitive_complexity": 5, "function_lines": 12},
            ],
        }
    ]
    assert quality_metrics.complexity_map(raw) == {
        ("theory/verify.py", "main"): 2,
        ("theory/verify.py", "helper"): 5,
    }


@pytest.mark.l2
def test_complexity_map_rejects_unknown_schema() -> None:
    """Schema drift must fail loudly instead of silently dropping entries."""
    with pytest.raises(ValueError, match="Unrecognized"):
        quality_metrics.complexity_map([{"unexpected": True}])


@pytest.mark.l1
def test_measure_files_line_counting_toggles(tmp_path: Path) -> None:
    """Blank and pure-comment lines obey the configured counting toggles."""
    source = tmp_path / "sample.py"
    source.write_text(
        "def f():\n    # comment\n\n    return 1\n",
        encoding="utf-8",
    )
    files_off, funcs_off = quality_metrics.measure_files(
        [str(tmp_path)],
        count_blank_lines=False,
        count_comment_lines=False,
        exclude_patterns=[],
    )
    files_on, funcs_on = quality_metrics.measure_files(
        [str(tmp_path)],
        count_blank_lines=True,
        count_comment_lines=True,
        exclude_patterns=[],
    )
    assert len(files_off) == 1
    assert files_off[0].function_count == 1
    assert files_off[0].lines == 2  # def + return
    assert funcs_off[0].lines == 2
    assert files_on[0].lines == 4  # + blank + comment
    assert funcs_on[0].lines == 4


@pytest.mark.l2
def test_measure_files_honors_exclude_patterns(tmp_path: Path) -> None:
    """fnmatch exclude patterns must drop matching files before measurement."""
    kept = tmp_path / "kept.py"
    dropped = tmp_path / "vendor_mod.py"
    kept.write_text("def ok():\n    return 0\n", encoding="utf-8")
    dropped.write_text("def skip_me():\n    return 1\n", encoding="utf-8")
    files, _ = quality_metrics.measure_files(
        [str(tmp_path)],
        count_blank_lines=False,
        count_comment_lines=False,
        exclude_patterns=["*/vendor_mod.py"],
    )
    assert [item.file_key for item in files] == [quality_metrics.as_file_key(kept)]


@pytest.mark.l1
def test_excluded_patterns() -> None:
    """excluded() matches POSIX keys against fnmatch patterns."""
    assert quality_metrics.excluded("tests/python/a.py", ["tests/**"])
    assert not quality_metrics.excluded("theory/a.py", ["tests/**"])


@pytest.mark.l1
def test_load_report_reads_json_list(tmp_path: Path) -> None:
    """load_report returns the JSON list payload for the gate."""
    report = tmp_path / "report.json"
    report.write_text(
        '[{"path":"a.py","function_name":"f","complexity":1,"file_name":"a.py"}]',
        encoding="utf-8",
    )
    assert quality_metrics.load_report(report)[0]["function_name"] == "f"


@pytest.mark.l1
def test_venv_executable_resolves_beside_interpreter() -> None:
    """venv_executable points at a sibling of sys.executable."""
    path = quality_metrics.venv_executable("python")
    assert path.parent == Path(sys.executable).parent
    assert path.name.startswith("python")


@pytest.mark.l1
@given(st.integers(min_value=0, max_value=40), st.integers(min_value=0, max_value=40))
def test_complexity_map_flat_roundtrip_property(complexity: int, unused: int) -> None:
    """Any non-negative flat complexity maps back without loss (property)."""
    del unused
    raw = [
        {
            "path": "a/b.py",
            "function_name": "f",
            "complexity": complexity,
            "file_name": "b.py",
        }
    ]
    assert quality_metrics.complexity_map(raw)[("a/b.py", "f")] == complexity


@pytest.mark.l1
@given(st.text(min_size=1, max_size=32).filter(lambda s: "/" not in s and "\\" not in s))
def test_as_file_key_idempotent_for_simple_names(name: str) -> None:
    """Simple relative names are stable under repeated as_file_key."""
    once = quality_metrics.as_file_key(name)
    assert quality_metrics.as_file_key(once) == once
