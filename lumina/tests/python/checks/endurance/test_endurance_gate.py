"""Endurance L5 gate branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.endurance import gate as end_gate


def test_disabled_returns_empty(tmp_path: Path) -> None:
    """enable=false short-circuits."""
    assert end_gate.endurance_violations({"endurance_standard": {"enable": False}}, root=tmp_path) == []


def test_partial_switches_and_caps(tmp_path: Path) -> None:
    """perf/latency/rounds and artifact failure branches."""
    proto = tmp_path / "proto.py"
    proto.write_text("pass\n", encoding="utf-8")
    standard = {
        "enable": True,
        "level": "L4",
        "require_perf_enable": True,
        "require_latency_cap": True,
        "require_protocol_warmup_timed": True,
        "require_endurance_tests": True,
        "require_min_fatigue_rounds": True,
        "max_latency_regression": 0.02,
        "min_fatigue_rounds": 50,
        "protocol_file": "proto.py",
        "protocol_markers": ["warmup"],
        "endurance_test_files": ["missing.py"],
        "endurance_markers": ["fatigue"],
    }
    config = {
        "endurance_standard": standard,
        "perf_standard": {"enable": False, "max_latency_regression": 0.05},
    }
    hits = end_gate.endurance_violations(config, root=tmp_path)
    assert any("perf_standard.enable" in item["target"] for item in hits)
    assert any("max_latency_regression" in item["target"] for item in hits)
    assert any("min_fatigue_rounds" in item["target"] for item in hits)
    assert any("缺少" in item["issue"] or "线索" in item["issue"] for item in hits)


def test_full_config_pass(tmp_path: Path) -> None:
    """Complete L5 endurance config against a mini tree passes."""
    (tmp_path / "tools" / "checks" / "performance").mkdir(parents=True)
    (tmp_path / "tools" / "checks" / "performance" / "protocol.py").write_text(
        "warmup timed WARMUP_RUNS TIMED_RUNS\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "python" / "product").mkdir(parents=True)
    (tmp_path / "tests" / "python" / "product" / "test_kv_endurance.py").write_text(
        "endurance fatigue FATIGUE_ROUNDS 100\n",
        encoding="utf-8",
    )
    config = {
        "endurance_standard": {
            "enable": True,
            "level": "L5",
            "require_perf_enable": True,
            "require_latency_cap": True,
            "require_protocol_warmup_timed": True,
            "require_endurance_tests": True,
            "require_min_fatigue_rounds": True,
            "max_latency_regression": 0.02,
            "min_fatigue_rounds": 100,
            "protocol_file": "tools/checks/performance/protocol.py",
            "protocol_markers": ["warmup", "timed", "WARMUP_RUNS", "TIMED_RUNS"],
            "endurance_test_files": ["tests/python/product/test_kv_endurance.py"],
            "endurance_markers": ["endurance", "fatigue", "FATIGUE_ROUNDS", "100"],
        },
        "perf_standard": {"enable": True, "max_latency_regression": 0.02},
    }
    assert end_gate.endurance_violations(config, root=tmp_path) == []


def test_switch_off_helpers(tmp_path: Path) -> None:
    """Disabled require_* helpers return empty."""
    std = {
        "enable": True,
        "level": "L4",
        "require_perf_enable": False,
        "require_latency_cap": False,
        "require_protocol_warmup_timed": False,
        "require_endurance_tests": False,
        "require_min_fatigue_rounds": False,
    }
    assert end_gate.endurance_violations({"endurance_standard": std}, root=tmp_path) == []


def test_main_paths(monkeypatch: Any) -> None:
    """main covers skip / pass / fail."""
    monkeypatch.setattr(end_gate, "load_config", lambda: {"endurance_standard": {"enable": False}})
    assert end_gate.main() == 0
    monkeypatch.setattr(end_gate, "load_config", lambda: {"endurance_standard": {"enable": True}})
    monkeypatch.setattr(end_gate, "endurance_violations", lambda _c: [])
    assert end_gate.main() == 0
    monkeypatch.setattr(
        end_gate,
        "endurance_violations",
        lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
    )
    assert end_gate.main() == 1
