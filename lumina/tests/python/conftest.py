"""pytest / Hypothesis entry; paths and profile numbers come from quality-gate.toml.

职责
====
1. 从 ``quality-gate.toml`` ``[cache]`` / ``[hypothesis]`` 加载配置并注册 profile。
2. 提供原生扩展 fixture：``luma_native`` / ``luma_cuda``（缺扩展时按测试 skip）。
3. L5 数值门辅助 ``ulp2_limit`` 见同目录 ``helpers.py``（勿从本文件 import）。

Hypothesis
==========
官方 pytest 插件不读取 pyproject 的 ``hypothesis_*`` ini 键
（HypothesisWorks/hypothesis#2434），因此 profile 真值源在 quality-gate.toml；
本文件只加载。切换：``HYPOTHESIS_PROFILE=ci`` 或 ``--hypothesis-profile ci``。
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from tools.cache_layout import load_cache_config, load_hypothesis_config, lumina_root, tool_cache_dir

_LUMINA = lumina_root()
_CACHE_CFG = load_cache_config(_LUMINA / "quality-gate.toml")
_HYP_CFG = load_hypothesis_config(_LUMINA / "quality-gate.toml")
_HYP_HOME = tool_cache_dir("hypothesis", _LUMINA, config=_CACHE_CFG)
# 须在 hypothesis 触盘前设置：仅改 database 仍会在默认家目录写 constants/tmp。
os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", str(_HYP_HOME))


def _load_hypothesis() -> tuple[Any, Any]:
    """Load hypothesis; fall back to (None, None) when it is not installed."""
    try:
        from hypothesis import settings
        from hypothesis.configuration import set_hypothesis_home_dir
        from hypothesis.database import DirectoryBasedExampleDatabase
    except ModuleNotFoundError:
        return None, None
    set_hypothesis_home_dir(_HYP_HOME)
    return settings, DirectoryBasedExampleDatabase


_HYP_SETTINGS, _HYP_DB = _load_hypothesis()


def _profile_kwargs(name: str) -> dict[str, Any]:
    """Map a ``[hypothesis.profiles.<name>]`` table into Hypothesis settings kwargs."""
    profiles = _HYP_CFG.get("profiles")
    if not isinstance(profiles, dict) or name not in profiles:
        raise KeyError(f"quality-gate.toml missing [hypothesis.profiles.{name}]")
    raw = dict(profiles[name])
    out: dict[str, Any] = {
        "max_examples": int(raw["max_examples"]),
        "deadline": int(raw["deadline_ms"]),
        "print_blob": bool(raw.get("print_blob", True)),
    }
    if raw.get("derandomize"):
        out["derandomize"] = True
    if raw.get("persist_examples") and _HYP_DB is not None:
        out["database"] = _HYP_DB(_HYP_HOME / "examples")
    return out


def _install_hypothesis_profiles() -> None:
    """Register profiles from quality-gate.toml; activate via HYPOTHESIS_PROFILE."""
    if _HYP_SETTINGS is None or _HYP_DB is None:
        return
    profiles = _HYP_CFG.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("quality-gate.toml [hypothesis] missing profiles")
    # 单遍注册：表名即 profile 名，避免代码内再列一份。
    for name in profiles:
        _HYP_SETTINGS.register_profile(name, **_profile_kwargs(name))
    default = str(_HYP_CFG.get("default_profile", "dev"))
    _HYP_SETTINGS.load_profile(os.getenv("HYPOTHESIS_PROFILE", default))


_install_hypothesis_profiles()


@pytest.fixture(scope="session")
def luma_native() -> Any:
    """Load ``_luma_native``; skip the requesting test when the extension is absent."""
    return pytest.importorskip("_luma_native")


@pytest.fixture(scope="session")
def luma_cuda() -> Any:
    """Load ``_luma_cuda``; skip the requesting test when the extension is absent."""
    return pytest.importorskip("_luma_cuda")
