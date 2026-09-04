"""Load unified cache paths from ``quality-gate.toml`` ``[cache]``.

配置优先：路径名只来自 TOML；本模块不内嵌目录字面量作为真值源。
complexipy 硬编码 vendor 目录名，正式入口以 ``cwd=<cache.root>`` 启动并回收
误落在仓库根的同名目录。
"""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path
from typing import Any

_GATE_TOML = "quality-gate.toml"


def lumina_root() -> Path:
    """Return the lumina/ package root (parent of tools/)."""
    return Path(__file__).resolve().parents[2]


def load_cache_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load ``[cache]`` from quality-gate.toml; raise when missing or incomplete."""
    path = config_path or (lumina_root() / _GATE_TOML)
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("cache")
    if not isinstance(section, dict):
        raise ValueError(f"{path}: missing [cache]")
    required = ("root", "hypothesis", "complexipy_vendor")
    missing = [key for key in required if key not in section]
    if missing:
        raise ValueError(f"{path} [cache] missing keys: {', '.join(missing)}")
    return dict(section)


def load_hypothesis_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load ``[hypothesis]`` (+ nested profiles) from quality-gate.toml."""
    path = config_path or (lumina_root() / _GATE_TOML)
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("hypothesis")
    if not isinstance(section, dict):
        raise ValueError(f"{path}: missing [hypothesis]")
    return dict(section)


def cache_root(
    base: Path | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> Path:
    """Return ``<base>/<cache.root>``, creating it when missing."""
    cfg = config or load_cache_config()
    root = (base or Path.cwd()) / str(cfg["root"])
    root.mkdir(parents=True, exist_ok=True)
    return root


def tool_cache_dir(
    tool_key: str,
    base: Path | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> Path:
    """Return ``<cache.root>/<cache.<tool_key>>`` for a named tool subdirectory."""
    cfg = config or load_cache_config()
    if tool_key not in cfg:
        raise KeyError(f"[cache] has no tool key {tool_key!r}")
    path = cache_root(base, config=cfg) / str(cfg[tool_key])
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_complexipy_cwd(
    base: Path | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> Path:
    """Return cwd for complexipy so its vendor cache stays under ``[cache].root``."""
    cfg = config or load_cache_config()
    root = cache_root(base, config=cfg)
    vendor = str(cfg["complexipy_vendor"])
    dest = root / vendor
    dest.mkdir(parents=True, exist_ok=True)
    _reclaim_stray((base or Path.cwd()) / vendor, dest)
    return root


def _reclaim_stray(stray: Path, dest: Path) -> None:
    """Move useful files from a top-level vendor dir into ``dest``, then remove it."""
    try:
        same = stray.resolve() == dest.resolve()
    except OSError:
        same = False
    if not stray.exists() or same:
        return
    if not stray.is_dir():
        stray.unlink(missing_ok=True)
        return
    # 单遍迁移：目标已存在则保留 dest，避免覆盖较新的增量缓存。
    for child in stray.iterdir():
        _move_stray_child(child, dest)
    shutil.rmtree(stray, ignore_errors=True)


def _move_stray_child(child: Path, dest: Path) -> None:
    """Move one stray cache entry into ``dest`` when the target name is unused."""
    target = dest / child.name
    if target.exists():
        return
    shutil.move(str(child), str(target))
