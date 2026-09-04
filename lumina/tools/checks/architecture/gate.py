"""Architecture gate: cycles, fan-out, inheritance depth, clone metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.checks.architecture.cycle import cyclic_dependency_count, max_fan_out
from tools.checks.architecture.dup import duplication_stats
from tools.checks.architecture.graph import build_import_graph
from tools.checks.architecture.inherit import max_inheritance_depth
from tools.checks.python.types import as_file_key, excluded


def architecture_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Compare architecture metrics against ``[thresholds]`` (fail closed)."""
    features = config.get("features", {})
    if not features.get("enable_architecture_check", True):
        return []
    thresholds = config["thresholds"]
    files = _project_files(config)
    graph = build_import_graph(files)
    cycles = cyclic_dependency_count(graph)
    fan_out, fan_mod = max_fan_out(graph)
    depth, depth_cls = max_inheritance_depth(files)
    blocks, ratio = duplication_stats(files)
    out: list[dict[str, str]] = []
    _append(out, "architecture", "循环依赖超限", cycles, thresholds["max_cyclic_dependencies"])
    _append(out, fan_mod or "architecture", "模块扇出超限", fan_out, thresholds["max_module_fan_out"])
    _append(out, depth_cls or "architecture", "继承深度超限", depth, thresholds["max_inheritance_depth"])
    _append(out, "architecture", "重复代码块超限", blocks, thresholds["max_duplicate_code_blocks"])
    _append(out, "architecture", "代码重复率超限", ratio, thresholds["max_code_duplication_ratio"])
    return out


def project_files(config: dict[str, Any]) -> list[tuple[str, Path]]:
    """Public alias for scan-root Python files used by architecture / HA gates."""
    return _project_files(config)


def _project_files(config: dict[str, Any]) -> list[tuple[str, Path]]:
    """List ``(file_key, path)`` under scan roots with exclusion patterns."""
    roots = list(config["scan"]["include_paths"])
    patterns = list(config.get("exclusions", {}).get("file_patterns", []))
    collected: list[tuple[str, Path]] = []
    # 单遍根目录：须与 quality_metrics 扫描对齐，避免架构门漏扫。
    for root in roots:
        collected.extend(_files_under(Path(root), patterns))
    return collected


def _files_under(base: Path, patterns: list[str]) -> list[tuple[str, Path]]:
    """Collect non-excluded ``*.py`` files under one scan root."""
    if not base.exists():
        return []
    out: list[tuple[str, Path]] = []
    # 单遍 rglob：须套 exclusion，避免 .cache 污染克隆/扇出。
    for path in sorted(base.rglob("*.py")):
        key = as_file_key(path)
        if excluded(key, patterns):
            continue
        out.append((key, path))
    return out


def _append(out: list[dict[str, str]], target: str, issue: str, current: int, limit: int) -> None:
    """Append a violation when ``current`` exceeds ``limit``."""
    if current > limit:
        out.append({"target": target, "issue": issue, "current": str(current), "limit": str(limit)})
