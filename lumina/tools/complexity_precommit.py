"""Cognitive-complexity gate executed by the root pre-commit hook.

提交前分级门禁的「认知复杂度强校验」层：只扫本次暂存的 lumina Python 文件，
复杂度数据来自 complexipy（多版本 schema 由 quality_metrics 归一化），阈值
取 quality-gate.toml 的单一真值源（max_cognitive_complexity）。超出即失败并
阻断提交；不执行全量四项门禁（那些下沉到 CI/手动入口 ``tools.run_quality_gate``）。

被 pre-commit 以 ``uv run --directory lumina python -m tools.complexity_precommit``
调用，argv 为暂存的 Python 文件路径（相对仓库根或绝对路径）。
"""

from __future__ import annotations

import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Dict

from tools.support import metrics as quality_metrics

_LUMINA_DIR = Path(__file__).resolve().parents[1]


def _load_threshold() -> int:
    """Read the cognitive-complexity threshold from quality-gate.toml."""
    config_path = _LUMINA_DIR / "quality-gate.toml"
    with config_path.open("rb") as handle:
        data: Dict[str, Any] = tomllib.load(handle)
    return int(data["thresholds"]["max_cognitive_complexity"])


def _staged_targets(argv: list[str]) -> list[str]:
    """Return staged python files from argv, or the configured scan roots.

    Pre-commit passes paths relative to the git root (``lumina/...``). This
    entrypoint runs with cwd ``lumina/``, so strip the leading ``lumina/`` when
    needed and resolve to existing files. Theory scripts are F1–F7 only and are
    excluded from the product cognitive-complexity hook.
    """
    if not argv:
        config_path = _LUMINA_DIR / "quality-gate.toml"
        with config_path.open("rb") as handle:
            data: Dict[str, Any] = tomllib.load(handle)
        roots = data["scan"]["include_paths"]
        return [str(_LUMINA_DIR / root) for root in roots]
    targets: list[str] = []
    # 必须跳过 theory/：产品认知复杂度钩子不得误伤 F1–F7 核验脚本。
    for raw in argv:
        path = _normalize_staged(raw)
        if not _is_theory(path):
            targets.append(str(path))
    return targets


def _is_theory(path: Path) -> bool:
    """Return True when ``path`` lives under ``lumina/theory/``."""
    try:
        path.resolve().relative_to(_LUMINA_DIR / "theory")
    except ValueError:
        return False
    return True


def _normalize_staged(path_str: str) -> Path:
    """把 pre-commit 传入路径映射到 lumina/ 下真实文件.

    pre-commit 常给仓库根相对路径 ``lumina/tools/foo.py``，而本模块 cwd 已是
    ``lumina/``，必须剥掉前缀 ``lumina/``，否则会拼成 ``lumina/lumina/...``。
    """
    path = Path(path_str)
    if path.is_file():
        return path.resolve()
    if path.parts[:1] == ("lumina",) and len(path.parts) > 1:
        candidate = _LUMINA_DIR.joinpath(*path.parts[1:])
        if candidate.is_file():
            return candidate.resolve()
    candidate = _LUMINA_DIR / path
    if candidate.is_file():
        return candidate.resolve()
    return path


def _report_excess(complexities: Dict[tuple[str, str], int], threshold: int) -> list[tuple[str, str, int]]:
    """Collect (file_key, name, complexity) records above the threshold."""
    return sorted(
        [(key[0], key[1], value) for key, value in complexities.items() if value > threshold],
        key=lambda item: item[2],
        reverse=True,
    )


def main() -> int:
    """Run the staged-file complexity scan and fail when any exceeds threshold."""
    threshold = _load_threshold()
    targets = _staged_targets(sys.argv[1:])
    if not targets:
        return 0
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as temp:
        output = Path(temp.name)
    try:
        quality_metrics.run_complexipy(targets, output)
        raw_report = quality_metrics.load_report(output)
    finally:
        output.unlink(missing_ok=True)
    excess = _report_excess(quality_metrics.complexity_map(raw_report), threshold)
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for file_key, name, value in excess:
        print(f"[COMPLEXITY] {file_key}::{name} = {value} (> {threshold})")
    if excess:
        print(f"[FAIL] complexity: {len(excess)} functions above {threshold}")
        return 1
    print(f"[PASS] complexity ≤ {threshold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
