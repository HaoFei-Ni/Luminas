"""Branch coverage for tools.checks.standards helpers."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.standards.artifacts import ArtifactKeys, artifact_hits
from tools.checks.standards.caps import feature_flag_hits, threshold_cap_hits
from tools.checks.standards.finding import finding
from tools.checks.standards.level import level_switch_hits
from tools.checks.standards.stage import run_standard_stage


def test_finding_defaults() -> None:
    """finding fills current/limit string fields."""
    assert finding("t", "i") == {"target": "t", "issue": "i", "current": "0", "limit": "1"}


def test_level_switch_non_l5_and_false() -> None:
    """Non-L5 skips; L5 false emits; L5 all-true passes."""
    assert level_switch_hits({"sec": {"level": "L4"}}, "sec", ("a",), "x") == []
    hits = level_switch_hits({"sec": {"level": "L5", "a": False}}, "sec", ("a",), "need")
    assert hits[0]["target"] == "sec.a"
    assert level_switch_hits({"sec": {"level": "L5", "a": True}}, "sec", ("a",), "need") == []


def test_feature_and_cap_branches() -> None:
    """feature_flag and threshold_cap cover on/off/loose/ok paths."""
    assert feature_flag_hits({}, {"s": False}, switch="s", feature_key="f", issue="i") == []
    assert (
        feature_flag_hits(
            {"features": {"f": True}},
            {"s": True},
            switch="s",
            feature_key="f",
            issue="i",
        )
        == []
    )
    miss = feature_flag_hits({}, {"s": True}, switch="s", feature_key="f", issue="need f")
    assert miss[0]["target"] == "features.f"
    specs = [("cap", "max_x")]
    assert threshold_cap_hits({}, {"cap": False}, specs, issue_prefix="P") == []
    assert (
        threshold_cap_hits(
            {"thresholds": {"max_x": 1}},
            {"cap": True, "max_x": 2},
            specs,
            issue_prefix="P",
        )
        == []
    )
    loose = threshold_cap_hits(
        {"thresholds": {"max_x": 9}},
        {"cap": True, "max_x": 2},
        specs,
        issue_prefix="P",
    )
    assert loose[0]["current"] == "9"


def test_artifact_hits(tmp_path: Path) -> None:
    """artifact_hits covers skip / missing / markerless / pass."""
    keys = ArtifactKeys(switch="on", files_key="f", markers_key="m", missing_issue="缺", marker_issue="线索")
    assert artifact_hits(tmp_path, {"on": False}, keys) == []
    bare = tmp_path / "bare.py"
    bare.write_text("pass\n", encoding="utf-8")
    ok = tmp_path / "ok.py"
    ok.write_text("cycle ok\n", encoding="utf-8")
    std = {"on": True, "f": ["missing.py", "bare.py", "ok.py"], "m": ["cycle"]}
    hits = artifact_hits(tmp_path, std, keys)
    assert any("缺" in item["issue"] for item in hits)
    assert any("线索" in item["issue"] for item in hits)
    assert not any(item["target"] == "ok.py" for item in hits)


def test_run_standard_stage(capsys: Any) -> None:
    """stage runner covers skip / pass / fail exits."""
    assert (
        run_standard_stage(
            section="s",
            stage="st",
            load_config=lambda: {"s": {"enable": False}},
            collect=lambda _c: [],
        )
        == 0
    )
    assert "跳过" in capsys.readouterr().out
    assert (
        run_standard_stage(
            section="s",
            stage="st",
            load_config=lambda: {"s": {"enable": True}},
            collect=lambda _c: [],
        )
        == 0
    )
    assert "PASS" in capsys.readouterr().out
    assert (
        run_standard_stage(
            section="s",
            stage="st",
            load_config=lambda: {"s": {"enable": True}},
            collect=lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
        )
        == 1
    )
    assert "FAIL" in capsys.readouterr().out
