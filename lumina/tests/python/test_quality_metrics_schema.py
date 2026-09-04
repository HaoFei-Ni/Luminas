"""L1: pure-Python quality_metrics path / schema unit tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from tools import quality_metrics


@pytest.mark.l1
def test_as_file_key_normalizes_separators() -> None:
    """Path keys must be POSIX-style so Windows and Unix reports compare equal."""
    assert quality_metrics.as_file_key(r"tests\python\a.py") == "tests/python/a.py"
    assert quality_metrics.as_file_key(Path("tests/python/a.py")) == "tests/python/a.py"


def test_as_file_key_strips_lumina_absolute_prefix() -> None:
    """Absolute complexipy paths under lumina/ collapse to repo-relative keys."""
    assert quality_metrics.as_file_key(r"//?/D:/data/Luminas/lumina/tools/a.py") == "tools/a.py"
    assert quality_metrics.as_file_key("/home/x/lumina/tools/a.py") == "tools/a.py"


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
def test_excluded_patterns() -> None:
    """excluded() matches POSIX keys against fnmatch patterns."""
    assert quality_metrics.excluded("tests/python/a.py", ["tests/**"])
    assert not quality_metrics.excluded("theory/a.py", ["tests/**"])


@pytest.mark.l1
def test_venv_executable_resolves_beside_interpreter() -> None:
    """venv_executable points at a sibling of sys.executable."""
    path = quality_metrics.venv_executable("python")
    assert path.parent == Path(sys.executable).parent
    assert path.name.startswith("python")
