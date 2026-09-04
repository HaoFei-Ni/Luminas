"""Configure and build the lumina CMake superproject (discovers CMake/Ninja)."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from tools.support.cache import lumina_root
from tools.support.dev_env import find_cmake, find_ninja, prepend_tool_bins_to_path
from tools.support.vcvars import run_via_vcvars


def _run(cmd: list[str], *, cwd: Path) -> None:
    print("[build]", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=cwd, check=False)  # noqa: S603
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _run_ctest(cmake: Path, build_dir: Path, *, cwd: Path) -> None:
    """Run ctest beside ``cmake`` or from PATH after a direct pipeline build."""
    ctest_name = "ctest.exe" if os.name == "nt" else "ctest"
    ctest = cmake.with_name(ctest_name)
    if ctest.is_file():
        resolved = ctest
    else:
        which = shutil.which("ctest")
        if not which:
            raise SystemExit("ctest not found next to cmake")
        resolved = Path(which)
    _run([str(resolved), "--test-dir", str(build_dir), "--output-on-failure"], cwd=cwd)


def _run_via_vcvars(steps: list[str], *, cwd: Path) -> None:
    """Delegate to ``tools.support.vcvars`` (kept name for call sites)."""
    run_via_vcvars(steps, cwd=cwd)


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
    _run_ctest(cmake, build_dir, cwd=root)


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
