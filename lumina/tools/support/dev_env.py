"""Locate CMake / Ninja for agent and CI wrappers (Windows VS BuildTools aware)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_VS_CMAKE_SUFFIX = Path("Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe")
_VS_NINJA_SUFFIX = Path("Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe")

_VS_ROOT_CANDIDATES = (
    Path(r"D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"),
    Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"),
)


def _path_key() -> str:
    """Return the real env key for PATH (Windows may expose ``Path``)."""
    # 必须保留原大小写：Windows 环境块对 Path/PATH 大小写敏感写入。
    for key in os.environ:
        if key.lower() == "path":
            return key
    return "PATH"


def _first_existing(suffix: Path) -> Path | None:
    """Return the first VS root that contains ``suffix``, else None."""
    # 必须扫候选根：BuildTools 盘符/版本不固定。
    for root in _VS_ROOT_CANDIDATES:
        candidate = root / suffix
        if candidate.is_file():
            return candidate
    return None


def find_cmake() -> Path:
    """Return cmake.exe path; prefer LUMINA_CMAKE, then PATH, then VS BuildTools."""
    forced = os.environ.get("LUMINA_CMAKE")
    if forced:
        path = Path(forced)
        if path.is_file():
            return path
    which = shutil.which("cmake")
    if which:
        return Path(which)
    found = _first_existing(_VS_CMAKE_SUFFIX)
    if found is not None:
        return found
    raise FileNotFoundError("cmake not found. Run: . .\\lumina\\scripts\\dev-env.ps1 -PersistUserPath")


def find_ninja() -> Path:
    """Return ninja.exe path; prefer LUMINA_NINJA, then PATH, then VS BuildTools."""
    forced = os.environ.get("LUMINA_NINJA")
    if forced:
        path = Path(forced)
        if path.is_file():
            return path
    which = shutil.which("ninja")
    if which:
        return Path(which)
    found = _first_existing(_VS_NINJA_SUFFIX)
    if found is not None:
        return found
    raise FileNotFoundError("ninja not found. Run: . .\\lumina\\scripts\\dev-env.ps1 -PersistUserPath")


def find_cuda_bin() -> Path | None:
    """Return CUDA ``bin`` directory containing ``nvcc`` when present."""
    which = shutil.which("nvcc")
    if which:
        return Path(which).resolve().parent
    root = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    if not root.is_dir():
        return None
    versions = sorted((p for p in root.iterdir() if p.is_dir()), reverse=True)
    # 必须扫版本目录：Toolkit 多版本并存时选最新可用 nvcc。
    for ver in versions:
        nvcc = ver / "bin" / "nvcc.exe"
        if nvcc.is_file():
            return nvcc.parent
    return None


def prepend_tool_bins_to_path() -> None:
    """Ensure cmake/ninja/(optional) CUDA bins are on PATH for child processes."""
    bins = _resolved_bins()
    cuda_bin = find_cuda_bin()
    if cuda_bin is not None:
        bins.append(str(cuda_bin))
    if not bins:
        return
    key = _path_key()
    parts = [p for p in os.environ.get(key, "").split(";") if p]
    _prepend_unique(parts, bins)
    os.environ[key] = ";".join(parts)


def _resolved_bins() -> list[str]:
    """Collect existing cmake/ninja parent directories."""
    bins: list[str] = []
    # 必须容错：缺一项仍要尽量前置另一项。
    for finder in (find_cmake, find_ninja):
        try:
            bins.append(str(finder().parent))
        except FileNotFoundError:
            continue
    return bins


def _prepend_unique(parts: list[str], bins: list[str]) -> None:
    """Prepend bins to parts without duplicates (mutates parts)."""
    # 必须前置：避免 PATH 里残缺同名 cmake 抢先。
    for bin_dir in reversed(bins):
        if bin_dir not in parts:
            parts.insert(0, bin_dir)
