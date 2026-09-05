"""Product / C boundary (L2 ugly-input) test presence for robustness L5."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — Path used for read_text/exists
from typing import Any

from tools.checks.robustness.finding import finding


def boundary_test_hits(root: Path, standard: dict[str, Any]) -> list[dict[str, str]]:
    """Require configured boundary test files to exist and carry L2 markers."""
    if not bool(standard.get("require_boundary_tests", False)):
        return []
    files = list(standard.get("boundary_files", []))
    markers = list(standard.get("boundary_markers", ["L2", "ERR_ARG", "pytest.mark.l2"]))
    out: list[dict[str, str]] = []
    # 单遍：每个边界用例文件独立裁决，避免漏扫。
    for rel in files:
        out.extend(_one_file_hits(root / rel, rel, markers))
    return out


def _one_file_hits(path: Path, rel: str, markers: list[str]) -> list[dict[str, str]]:
    """Check one boundary test file for existence and marker coverage."""
    if not path.is_file():
        return [finding(rel, "缺少鲁棒性/边界测试文件（L2 丑输入）")]
    text = path.read_text(encoding="utf-8", errors="replace")
    # 必须命中至少一枚 L2 线索：否则文件存在但未测容错。
    if any(marker in text for marker in markers):
        return []
    return [finding(rel, f"边界测试缺少 L2/容错线索（须含 {'/'.join(markers)}）")]
