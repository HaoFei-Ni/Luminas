"""Full quality-gate entry for CI and manual runs (not the pre-commit hook).

工作目录无关：始终以 lumina/ 为根执行：

1. complexipy + tools.ci_quality_gate（Python 四项门禁）
2. tools.c_quality_gate（C/CUDA 结构度量，补齐 kernel/algorithm 盲区）

提交前的秒级认知复杂度校验走 tools.complexity_precommit，勿改本文件用途。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from tools import quality_metrics

_LUMINA_DIR = Path(__file__).resolve().parents[1]


def _load_config() -> dict[str, Any]:
    """Load quality-gate.toml from the lumina directory."""
    config_path = _LUMINA_DIR / "quality-gate.toml"
    with config_path.open("rb") as handle:
        return dict(tomllib.load(handle))


def _run_module(module: str) -> int:
    """Run ``python -m <module>`` in the lumina directory."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", module],
        check=False,
    )
    return result.returncode


def main() -> int:
    """Run Python then C quality gates; fail if either fails."""
    os.chdir(_LUMINA_DIR)
    config = _load_config()
    targets = list(config["scan"]["include_paths"])
    report_path = Path(config["report"]["json_report_path"])
    quality_metrics.run_complexipy(targets, report_path)
    py_code = _run_module("tools.ci_quality_gate")
    c_code = _run_module("tools.c_quality_gate")
    if py_code != 0 or c_code != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
