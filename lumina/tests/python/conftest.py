"""pytest / Hypothesis entry; paths and profile numbers come from quality-gate.toml.

职责
====
1. 从 ``quality-gate.toml`` ``[cache]`` / ``[hypothesis]`` 加载配置并注册 profile。
2. 提供原生扩展 fixture：``luma_native`` / ``luma_baseline`` / ``luma_cuda``（缺扩展时按测试 skip）。
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

from tools.support.cache import load_cache_config, load_hypothesis_config, lumina_root, tool_cache_dir
from tools.support.hypothesis import profile_settings_kwargs

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

    def _db() -> Any:
        assert _HYP_DB is not None
        return _HYP_DB(_HYP_HOME / "examples")

    factory = _db if _HYP_DB is not None else None
    return profile_settings_kwargs(raw, database_factory=factory)


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

# 构建产物目录：pytest 需能 import _luma_native / _luma_baseline。
_BUILD_WRAPPER = _LUMINA.parent / "outputs" / "build" / "lumina" / "wrapper"
if _BUILD_WRAPPER.is_dir():
    import sys

    path = str(_BUILD_WRAPPER.resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def luma_native() -> Any:
    """Load ``_luma_native`` (product KV); skip when the extension is absent."""
    return pytest.importorskip("_luma_native")


@pytest.fixture(scope="session")
def luma_baseline() -> Any:
    """Load ``_luma_baseline`` (lossy only); skip when the extension is absent."""
    return pytest.importorskip("_luma_baseline")


@pytest.fixture(scope="session")
def luma_cuda() -> Any:
    """Load ``_luma_cuda``; skip the requesting test when the extension is absent."""
    return pytest.importorskip("_luma_cuda")
