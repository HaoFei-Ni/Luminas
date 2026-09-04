"""Full quality-gate entry (CI / manual; not a pre-commit hook).

Always runs with cwd = ``lumina/`` so report paths stay stable:

1. ``ruff check`` (includes pydocstyle D);
2. complexipy → ``tools.reporting.python_gate`` (Python structure + inline why);
3. ``tools.checks.native.gate`` (C/CUDA structure + inline why);
4. ``tools.checks.naming.gate`` (LUM-ENG-101 naming);
5. ``tools.checks.performance.gate`` (L4: 2+5 timed runs, ≤2% regression).

Commit-time cognitive complexity uses ``tools.complexity_precommit``; do not
fold this full suite into a hook.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from tools.support import metrics as quality_metrics

_LUMINA_DIR = Path(__file__).resolve().parents[1]


def _load_config() -> dict[str, Any]:
    """Load ``lumina/quality-gate.toml`` (scan + report single source of truth)."""
    config_path = _LUMINA_DIR / "quality-gate.toml"
    with config_path.open("rb") as handle:
        return dict(tomllib.load(handle))


def _run_module(module: str) -> int:
    """Run ``python -m <module>`` with cwd already set to ``lumina/``."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", module],
        check=False,
    )
    return result.returncode


def _run_ruff() -> int:
    """Lint ``tools`` and ``tests`` with ruff (includes docstring D)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "ruff", "check", "tools", "tests"],
        check=False,
    )
    if result.returncode != 0:
        print("[FAIL] ruff check")
        return result.returncode
    print("[PASS] ruff check")
    return 0


def _print_summary(stages: list[tuple[str, int]]) -> int:
    """Print a stage table and return 0 only when every stage passed."""
    print("")
    print("| Stage | Status |")
    print("|---|---|")
    failed = 0
    # 必须汇总各阶段：CI 需要一眼看到失败点，避免只看末尾 exit code。
    for name, code in stages:
        status = "PASS" if code == 0 else f"FAIL ({code})"
        if code != 0:
            failed = 1
        print(f"| {name} | {status} |")
    verdict = "PASS" if failed == 0 else "FAIL"
    print(f"[GATE] overall={verdict}")
    return failed


def main() -> int:
    """Ruff → Python → C → naming → L4 perf; fail closed on any gate."""
    os.chdir(_LUMINA_DIR)
    config = _load_config()
    targets = list(config["scan"]["include_paths"])
    report_path = Path(config["report"]["json_report_path"])
    ruff_code = _run_ruff()
    # complexipy must write JSON before reporting.python_gate reads it.
    quality_metrics.run_complexipy(targets, report_path)
    stages = [
        ("ruff", ruff_code),
        ("python-structure", _run_module("tools.reporting.python_gate")),
        ("c-structure", _run_module("tools.checks.native.gate")),
        ("naming", _run_module("tools.checks.naming.gate")),
        ("perf-l4", _run_module("tools.checks.performance.gate")),
    ]
    return _print_summary(stages)


if __name__ == "__main__":
    raise SystemExit(main())
