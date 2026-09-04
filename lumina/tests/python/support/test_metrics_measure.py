"""L1 / L2: quality_metrics measurement and Hypothesis property tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hypothesis import given, strategies as st

from tools.support import metrics as quality_metrics

if TYPE_CHECKING:
    from pathlib import Path


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
def test_load_report_reads_json_list(tmp_path: Path) -> None:
    """load_report returns the JSON list payload for the gate."""
    report = tmp_path / "report.json"
    report.write_text(
        '[{"path":"a.py","function_name":"f","complexity":1,"file_name":"a.py"}]',
        encoding="utf-8",
    )
    assert quality_metrics.load_report(report)[0]["function_name"] == "f"


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
