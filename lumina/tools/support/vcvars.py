"""MSVC vcvars discovery and batch execution for ``tools.run_build``."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def run_via_vcvars(steps: list[str], *, cwd: Path) -> None:
    """Write a temp .bat that calls vcvarsall then runs build steps (stable quoting)."""
    vcvars = find_vcvars()
    if vcvars is None:
        raise SystemExit("vcvarsall.bat not found; install VS Build Tools C++ workload")
    lines = [
        "@echo off",
        "setlocal",
        f'call "{vcvars}" x64',
        "if errorlevel 1 exit /b 1",
        *steps,
        "exit /b %ERRORLEVEL%",
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".bat", delete=False, encoding="utf-8") as handle:
        handle.write("\r\n".join(lines) + "\r\n")
        bat = Path(handle.name)
    try:
        exec_vcvars_bat(bat, steps, cwd=cwd)
    finally:
        bat.unlink(missing_ok=True)


def find_vcvars() -> Path | None:
    """Locate vcvarsall.bat from LUMINA_VCVARS or known VS BuildTools roots."""
    forced = os.environ.get("LUMINA_VCVARS")
    if forced and Path(forced).is_file():
        return Path(forced)
    # 必须扫候选：BuildTools 安装根盘符不固定。
    for root in (
        Path(r"D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"),
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools"),
    ):
        candidate = root / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
        if candidate.is_file():
            return candidate
    return None


def exec_vcvars_bat(bat: Path, steps: list[str], *, cwd: Path) -> None:
    """Echo steps and run the vcvars wrapper batch."""
    print("[build] via", bat, flush=True)
    # 必须逐条回显：vcvars 脚本失败时便于定位卡在哪一步。
    for step in steps:
        print("[build]", step, flush=True)
    completed = subprocess.run(["cmd", "/c", str(bat)], cwd=cwd, check=False)  # noqa: S603, S607
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
