"""Cover ``run_complexipy`` success and empty-report failure branches."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from types import SimpleNamespace
from typing import Any

from tools.support import metrics as quality_metrics


def test_run_complexipy_writes_report(monkeypatch: Any, tmp_path: Path) -> None:
    """Successful complexipy invocation leaves a non-empty JSON report."""
    report = tmp_path / "out" / "complexipy.json"

    def _fake_run(command: list[str], cwd: Path, check: bool) -> SimpleNamespace:  # noqa: ARG001
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("[]", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(quality_metrics, "prepare_complexipy_cwd", lambda: tmp_path)
    monkeypatch.setattr(quality_metrics, "venv_executable", lambda _name: "complexipy")
    monkeypatch.setattr(quality_metrics.subprocess, "run", _fake_run)
    quality_metrics.run_complexipy(["tools"], report)
    assert report.exists() and report.stat().st_size > 0


def test_run_complexipy_rejects_empty_report(monkeypatch: Any, tmp_path: Path) -> None:
    """Missing or empty JSON report raises RuntimeError."""
    report = tmp_path / "missing.json"
    monkeypatch.setattr(quality_metrics, "prepare_complexipy_cwd", lambda: tmp_path)
    monkeypatch.setattr(quality_metrics, "venv_executable", lambda _name: "complexipy")
    monkeypatch.setattr(
        quality_metrics.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=1),
    )
    try:
        quality_metrics.run_complexipy(["tools"], report)
        raised = False
    except RuntimeError:
        raised = True
    assert raised
