"""Shared quality-gate.toml loader for check entrypoints."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any


def load_quality_gate(config_path: str = "quality-gate.toml") -> dict[str, Any]:
    """Load quality-gate.toml from the lumina working directory."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    with path.open("rb") as handle:
        return dict(tomllib.load(handle))
