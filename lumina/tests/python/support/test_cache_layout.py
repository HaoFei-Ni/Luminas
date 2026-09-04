"""Unit tests: cache helpers read quality-gate.toml (config-first)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tools.support.cache import cache_root, load_cache_config, prepare_complexipy_cwd, tool_cache_dir

if TYPE_CHECKING:
    from pathlib import Path

_MIN_CACHE = """
[cache]
root = ".cache"
pytest = "pytest"
mypy = "mypy"
ruff = "ruff"
hypothesis = "hypothesis"
uv = "uv"
complexipy_vendor = ".complexipy_cache"
"""


def _write_gate(tmp_path: Path) -> Path:
    path = tmp_path / "quality-gate.toml"
    path.write_text(_MIN_CACHE, encoding="utf-8")
    return path


def test_load_cache_config_requires_root(tmp_path: Path) -> None:
    """Missing [cache].root must raise rather than invent a default path."""
    gate = tmp_path / "quality-gate.toml"
    gate.write_text('[cache]\nhypothesis = "h"\ncomplexipy_vendor = "v"\n', encoding="utf-8")
    try:
        load_cache_config(gate)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_cache_root_uses_config_name(tmp_path: Path) -> None:
    """cache_root must use [cache].root from the provided config dict."""
    cfg = load_cache_config(_write_gate(tmp_path))
    root = cache_root(tmp_path, config=cfg)
    assert root == tmp_path / ".cache"
    assert root.is_dir()


def test_prepare_complexipy_cwd_reclaims_stray(tmp_path: Path) -> None:
    """Top-level vendor dir is moved under [cache].root then removed."""
    cfg = load_cache_config(_write_gate(tmp_path))
    vendor = str(cfg["complexipy_vendor"])
    stray = tmp_path / vendor
    stray.mkdir()
    (stray / "keep.bin").write_bytes(b"x")

    cwd = prepare_complexipy_cwd(tmp_path, config=cfg)

    assert cwd == tmp_path / str(cfg["root"])
    assert not stray.exists()
    assert (cwd / vendor / "keep.bin").read_bytes() == b"x"


def test_tool_cache_dir_joins_root_and_key(tmp_path: Path) -> None:
    """tool_cache_dir joins [cache].root with the named tool subdirectory."""
    cfg = load_cache_config(_write_gate(tmp_path))
    path = tool_cache_dir("hypothesis", tmp_path, config=cfg)
    assert path == tmp_path / ".cache" / "hypothesis"
