"""Configure and build the lumina CMake superproject (discovers CMake/Ninja)."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.support.cache import lumina_root
from tools.support.dev_env import find_cmake, find_ninja, prepend_tool_bins_to_path


def _vcvars() -> Path | None:
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


def _run(cmd: list[str], *, cwd: Path) -> None:
    print("[build]", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=cwd, check=False)  # noqa: S603
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _run_via_vcvars(steps: list[str], *, cwd: Path) -> None:
    """Write a temp .bat that calls vcvarsall then runs build steps (stable quoting)."""
    vcvars = _vcvars()
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
        print("[build] via", bat, flush=True)
        # 必须逐条回显：vcvars 脚本失败时便于定位卡在哪一步。
        for step in steps:
            print("[build]", step, flush=True)
        completed = subprocess.run(["cmd", "/c", str(bat)], cwd=cwd, check=False)  # noqa: S603, S607
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)
    finally:
        bat.unlink(missing_ok=True)


def _pybind11_dir() -> Path | None:
    try:
        import pybind11
    except ImportError:
        return None
    return Path(pybind11.get_cmake_dir())


def _prepare_cmake() -> Path:
    """Discover tools and export env vars used by Ninja/CMake children."""
    prepend_tool_bins_to_path()
    cmake = find_cmake()
    ninja = find_ninja()
    os.environ.setdefault("CMAKE_GENERATOR", "Ninja")
    os.environ["CMAKE_MAKE_PROGRAM"] = str(ninja)
    os.environ["LUMINA_CMAKE"] = str(cmake)
    os.environ["LUMINA_NINJA"] = str(ninja)
    return cmake


def _msvc_pipeline(cmake: Path, preset: str, build_dir: Path, run_tests: bool) -> list[str]:
    """Build cmd.exe steps for configure/build/(optional)ctest under vcvars."""
    pybind_dir = _pybind11_dir()
    configure = f'"{cmake}" --preset {preset}'
    if pybind_dir is not None:
        # 必须显式传入：VS cmake 默认找不到 uv venv 的 pybind11。
        configure += f' -Dpybind11_DIR="{pybind_dir}"'
    steps = [configure, "if errorlevel 1 exit /b 1", f'"{cmake}" --build "{build_dir}"']
    if not run_tests:
        return steps
    ctest = cmake.with_name("ctest.exe")
    steps.extend(
        [
            "if errorlevel 1 exit /b 1",
            f'"{ctest}" --test-dir "{build_dir}" --output-on-failure',
        ]
    )
    return steps


def _direct_pipeline(cmake: Path, preset: str, build_dir: Path, run_tests: bool) -> None:
    """Configure/build/(optional)ctest when ``cl`` is already on PATH."""
    root = lumina_root()
    pybind_dir = _pybind11_dir()
    cfg_cmd = [str(cmake), "--preset", preset]
    if pybind_dir is not None:
        cfg_cmd.append(f"-Dpybind11_DIR={pybind_dir}")
    _run(cfg_cmd, cwd=root)
    _run([str(cmake), "--build", str(build_dir)], cwd=root)
    if not run_tests:
        return
    ctest = cmake.with_name("ctest.exe" if os.name == "nt" else "ctest")
    if not ctest.is_file():
        which = shutil.which("ctest")
        if not which:
            raise SystemExit("ctest not found next to cmake")
        ctest = Path(which)
    _run([str(ctest), "--test-dir", str(build_dir), "--output-on-failure"], cwd=root)


def main(argv: list[str] | None = None) -> int:
    """CLI entry: configure (preset) then build; optional ctest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", default="windows-ninja", help="CMake configure preset")
    parser.add_argument("--test", action="store_true", help="Run ctest after build")
    parser.add_argument("--cuda", action="store_true", help="Use windows-ninja-cuda preset")
    args = parser.parse_args(argv)

    cmake = _prepare_cmake()
    root = lumina_root()
    preset = "windows-ninja-cuda" if args.cuda else args.preset
    build_dir = (root.parent / "outputs" / "build" / "lumina").resolve()
    needs_vc = shutil.which("cl") is None and os.name == "nt"
    if needs_vc:
        _run_via_vcvars(_msvc_pipeline(cmake, preset, build_dir, args.test), cwd=root)
    else:
        _direct_pipeline(cmake, preset, build_dir, args.test)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
