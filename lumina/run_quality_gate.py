"""Full quality-gate entry for CI and manual runs (not the pre-commit hook).

工作目录无关：始终以 lumina/ 为根执行「complexipy 扫描 + ci_quality_gate.py」。

- complexipy 目标取 quality-gate.toml 的 [scan].include_paths，与门禁 AST
  扫描共用同一真值源，输出到 [report].json_report_path；
- ci_quality_gate.py 读取同一 JSON，执行全量四项校验并产出健康度报告。

提交前的秒级认知复杂度校验走 complexity_precommit.py，勿改本文件用途。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict

import quality_metrics

_LUMINA_DIR = Path(__file__).resolve().parent


def _load_config() -> Dict[str, Any]:
    """Load quality-gate.toml from the lumina directory."""
    config_path = _LUMINA_DIR / "quality-gate.toml"
    with config_path.open("rb") as handle:
        return dict(tomllib.load(handle))


def main() -> int:
    """Run complexipy then the four-check gate; propagate the exit code."""
    os.chdir(_LUMINA_DIR)
    config = _load_config()
    targets = list(config["scan"]["include_paths"])
    report_path = Path(config["report"]["json_report_path"])
    quality_metrics.run_complexipy(targets, report_path)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "ci_quality_gate.py"], check=False
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
