"""Artifact file + marker presence checks for L5 standard gates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 — Path used for is_file/read_text
from typing import Any

from tools.checks.standards.finding import finding


@dataclass(frozen=True)
class ArtifactKeys:
    """Keys and messages for one artifact presence check."""

    switch: str
    files_key: str
    markers_key: str
    missing_issue: str
    marker_issue: str


def artifact_hits(root: Path, standard: dict[str, Any], keys: ArtifactKeys) -> list[dict[str, str]]:
    """Require configured files to exist and carry at least one marker."""
    if not bool(standard.get(keys.switch, False)):
        return []
    files = list(standard.get(keys.files_key, []))
    markers = list(standard.get(keys.markers_key, []))
    out: list[dict[str, str]] = []
    # 单遍：每个制品文件独立裁决，避免漏扫。
    for rel in files:
        out.extend(_one_file(root / rel, rel, markers, keys.missing_issue, keys.marker_issue))
    return out


def _one_file(
    path: Path,
    rel: str,
    markers: list[str],
    missing_issue: str,
    marker_issue: str,
) -> list[dict[str, str]]:
    """Check one artifact for existence and marker coverage."""
    if not path.is_file():
        return [finding(rel, missing_issue)]
    text = path.read_text(encoding="utf-8", errors="replace")
    # 必须命中至少一枚线索：否则文件存在但未覆盖目标档位语义。
    if any(marker in text for marker in markers):
        return []
    return [finding(rel, marker_issue)]
