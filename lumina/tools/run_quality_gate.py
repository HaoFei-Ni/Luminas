"""全量质量门禁入口（CI/手动；不是 pre-commit 钩子）.

始终以 ``lumina/`` 为根执行，避免从仓库根跑时路径漂移：

1. ``ruff check``（含 pydocstyle D，注释/文档最高档）；
2. complexipy + ``tools.ci_quality_gate``（Python 结构 + 行内 why）；
3. ``tools.c_quality_gate``（C/CUDA 结构 + 行内 why）；
4. ``tools.naming_gate``（LUM-ENG-101 命名最高档）；
5. ``tools.perf_gate``（eng-standard L4 性能最高档：2+5、≤2% 回归）。

提交前秒级认知复杂度走 ``tools.complexity_precommit``，勿把全量门禁塞进 hook。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from tools import quality_metrics

# 本文件在 tools/ 下，父目录即 lumina/。
_LUMINA_DIR = Path(__file__).resolve().parents[1]


def _load_config() -> dict[str, Any]:
    """加载 lumina/quality-gate.toml（扫描范围与报告路径的单一真值源）."""
    config_path = _LUMINA_DIR / "quality-gate.toml"
    with config_path.open("rb") as handle:
        return dict(tomllib.load(handle))


def _run_module(module: str) -> int:
    """在当前进程 cwd（已 chdir 到 lumina）下跑 ``python -m <module>``."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", module],
        check=False,
    )
    return result.returncode


def _run_ruff() -> int:
    """最高档：ruff lint（含 D docstring）扫 Python 生产与测试树."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "ruff", "check", "tools", "tests"],
        check=False,
    )
    if result.returncode != 0:
        print("❌ [RUFF-FAIL] ruff check（含 docstring D）未通过")
        return result.returncode
    print("✅ [RUFF-PASS] ruff check 通过")
    return 0


def main() -> int:
    """Ruff → Python → C → naming → L4 perf; fail closed on any gate."""
    os.chdir(_LUMINA_DIR)
    config = _load_config()
    targets = list(config["scan"]["include_paths"])
    report_path = Path(config["report"]["json_report_path"])
    ruff_code = _run_ruff()
    # complexipy 必须先写 JSON，ci_quality_gate 再读；顺序不可颠倒。
    quality_metrics.run_complexipy(targets, report_path)
    py_code = _run_module("tools.ci_quality_gate")
    c_code = _run_module("tools.c_quality_gate")
    name_code = _run_module("tools.naming_gate")
    perf_code = _run_module("tools.perf_gate")
    if ruff_code != 0 or py_code != 0 or c_code != 0 or name_code != 0 or perf_code != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
