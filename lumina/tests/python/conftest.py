"""pytest / Hypothesis configuration entry point for lumina/tests/python.

职责
====
1. 注册 Hypothesis profile（dev / ci），见下方说明。
2. 提供原生扩展 fixture：``luma_native`` / ``luma_cuda``（缺扩展时按测试 skip）。
3. L5 数值门辅助 ``ulp2_limit`` 见同目录 ``helpers.py``（勿从本文件 import）。

Hypothesis
==========
官方 pytest 插件不读取 pyproject 的 ``hypothesis_*`` ini 键
（HypothesisWorks/hypothesis#2434），因此项目级默认值只能经
``settings.register_profile`` 在此声明，再通过环境变量 ``HYPOTHESIS_PROFILE``
或 ``pytest --hypothesis-profile <name>`` 选择。

profile 一览
============
dev
    本地默认。随机搜索 + 较大样本预算；反例与最小化中间态持久化到
    ``test/.cache/hypothesis``，避免默认在 CWD 生成 ``.hypothesis``。
ci
    CI 确定性。``derandomize=true``：每次 CI 每个测试的输入序列逐字节一致；
    语义上隐含 ``database=None``，CI 不读写示例库。

按需覆盖
========
- 深挖：``HYPOTHESIS_PROFILE=dev pytest -k <name>``，单测临时
  ``@settings(max_examples=5000, deadline=None)``。
- 换档：``HYPOTHESIS_PROFILE=ci uv run pytest`` 或 ``--hypothesis-profile ci``。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

# hypothesis 是可选的：未安装时跳过 profile 注册，非属性测试仍可运行。
# 用函数返回元组，规避 mypy strict 的 no-redef。


def _load_hypothesis() -> tuple[Any, Any]:
    """Load hypothesis; fall back to (None, None) when it is not installed."""
    try:
        from hypothesis import settings
        from hypothesis.database import DirectoryBasedExampleDatabase
    except ModuleNotFoundError:
        return None, None
    return settings, DirectoryBasedExampleDatabase


_HYP_SETTINGS, _HYP_DB = _load_hypothesis()


def _install_hypothesis_profiles() -> None:
    """Register project profiles and activate per HYPOTHESIS_PROFILE (default dev)."""
    if _HYP_SETTINGS is None or _HYP_DB is None:
        return

    # 锚定 lumina/ 根（conftest.py 位于 lumina/tests/python/，向上三级），
    # 与 pytest cache_dir / mypy cache_dir 共用 test/.cache 收敛约定。
    cache_root = Path(__file__).resolve().parents[2] / "test" / ".cache"

    _HYP_SETTINGS.register_profile(
        "dev",
        max_examples=1000,
        deadline=3000,
        print_blob=True,
        database=_HYP_DB(cache_root / "hypothesis"),
    )
    _HYP_SETTINGS.register_profile(
        "ci",
        max_examples=300,
        deadline=3000,
        print_blob=True,
        derandomize=True,
    )
    _HYP_SETTINGS.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


_install_hypothesis_profiles()


@pytest.fixture(scope="session")
def luma_native() -> Any:
    """Load ``_luma_native``; skip the requesting test when the extension is absent."""
    return pytest.importorskip("_luma_native")


@pytest.fixture(scope="session")
def luma_cuda() -> Any:
    """Load ``_luma_cuda``; skip the requesting test when the extension is absent."""
    return pytest.importorskip("_luma_cuda")
