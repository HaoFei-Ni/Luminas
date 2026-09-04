"""Unit tests for architecture graph / inheritance / clone gate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tools.checks.architecture.cycle import cyclic_dependency_count, max_fan_out
from tools.checks.architecture.dup import duplication_stats
from tools.checks.architecture.gate import architecture_violations
from tools.checks.architecture.graph import build_import_graph, module_name
from tools.checks.architecture.inherit import max_inheritance_depth

if TYPE_CHECKING:
    from pathlib import Path


def test_module_name_maps_init_to_package() -> None:
    """``tools/pkg/__init__.py`` becomes ``tools.pkg``."""
    assert module_name("tools/pkg/__init__.py") == "tools.pkg"


def test_cyclic_dependency_detected(tmp_path: Path) -> None:
    """A ↔ B import cycle yields count 1."""
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text("from tools.b import x\nx = 1\n", encoding="utf-8")
    b.write_text("from tools.a import x\nx = 2\n", encoding="utf-8")
    files = [("tools/a.py", a), ("tools/b.py", b)]
    assert cyclic_dependency_count(build_import_graph(files)) == 1


def test_fan_out_counts_distinct_imports(tmp_path: Path) -> None:
    """Fan-out equals distinct first-party modules imported."""
    hub = tmp_path / "hub.py"
    leaf = tmp_path / "leaf.py"
    hub.write_text("from tools.leaf import z\nz = 1\n", encoding="utf-8")
    leaf.write_text("z = 0\n", encoding="utf-8")
    files = [("tools/hub.py", hub), ("tools/leaf.py", leaf)]
    fan, name = max_fan_out(build_import_graph(files))
    assert fan == 1
    assert name == "tools.hub"


def test_inheritance_depth_counts_chain(tmp_path: Path) -> None:
    """A→B→C yields depth 3 for C."""
    path = tmp_path / "chain.py"
    path.write_text("class A: pass\nclass B(A): pass\nclass C(B): pass\n", encoding="utf-8")
    depth, locator = max_inheritance_depth([("tools/chain.py", path)])
    assert depth == 3
    assert locator.endswith(".C")


def test_duplication_stats_flags_cloned_tiles(tmp_path: Path) -> None:
    """Identical 6-line tiles across files count as one duplicate block group."""
    body = "\n".join(f"v{i} = {i}" for i in range(6)) + "\n"
    left = tmp_path / "left.py"
    right = tmp_path / "right.py"
    left.write_text(body, encoding="utf-8")
    right.write_text(body, encoding="utf-8")
    blocks, ratio = duplication_stats([("tools/left.py", left), ("tools/right.py", right)])
    assert blocks == 1
    assert ratio > 0


def test_architecture_violations_respect_feature_flag() -> None:
    """Disabled architecture check returns no violations."""
    config = {"features": {"enable_architecture_check": False}, "thresholds": {}}
    assert architecture_violations(config) == []
