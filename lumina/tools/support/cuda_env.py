"""Windows CUDA toolkit discovery for build wrappers."""

from __future__ import annotations

import shutil
from pathlib import Path


def find_cuda_bin() -> Path | None:
    """Return CUDA ``bin`` directory containing ``nvcc`` when present."""
    which = shutil.which("nvcc")
    if which:
        return Path(which).resolve().parent
    return _nvcc_from_toolkit_root(Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"))


def _nvcc_bin_of(version_dir: Path) -> Path | None:
    """Return ``bin`` when ``version_dir`` is a toolkit dir with nvcc."""
    nvcc = version_dir / "bin" / "nvcc.exe"
    if version_dir.is_dir() and nvcc.is_file():
        return nvcc.parent
    return None


def _nvcc_from_toolkit_root(root: Path) -> Path | None:
    """Pick newest CUDA toolkit version directory that contains ``nvcc.exe``."""
    if not root.is_dir():
        return None
    # 必须扫版本目录：Toolkit 多版本并存时选最新可用 nvcc。
    for ver in sorted(root.iterdir(), reverse=True):
        found = _nvcc_bin_of(ver)
        if found is not None:
            return found
    return None
