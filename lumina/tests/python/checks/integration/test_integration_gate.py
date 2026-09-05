"""Integration L5 gate branch coverage."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pytest tmp_path annotations
from typing import Any

from tools.checks.integration import gate as int_gate


def test_disabled_returns_empty(tmp_path: Path) -> None:
    """enable=false short-circuits."""
    assert int_gate.integration_violations({"integration_standard": {"enable": False}}, root=tmp_path) == []


def test_missing_artifacts(tmp_path: Path) -> None:
    """Absent integration files are flagged."""
    config = {
        "integration_standard": {
            "enable": True,
            "level": "L4",
            "require_python_l3_tests": True,
            "require_c_product_tests": True,
            "require_native_marker": False,
            "require_roundtrip_marker": False,
            "require_bind_kernel_agreement": False,
            "python_integration_files": ["missing_py.py"],
            "python_integration_markers": ["l3"],
            "c_integration_files": ["missing_c.c"],
            "c_integration_markers": ["L1"],
        }
    }
    hits = int_gate.integration_violations(config, root=tmp_path)
    assert len(hits) >= 2


def test_full_config_pass(tmp_path: Path) -> None:
    """Complete L5 integration config against a mini tree passes."""
    py = tmp_path / "tests" / "python" / "product"
    py.mkdir(parents=True)
    (py / "test_kernels.py").write_text("@pytest.mark.l3\n@pytest.mark.native\nroundtrip\n", encoding="utf-8")
    c_dir = tmp_path / "tests" / "c"
    c_dir.mkdir(parents=True)
    (c_dir / "test_luma_kv.c").write_text("/* L1 L5 encode decode */\n", encoding="utf-8")
    config = {
        "integration_standard": {
            "enable": True,
            "level": "L5",
            "require_python_l3_tests": True,
            "require_c_product_tests": True,
            "require_native_marker": True,
            "require_roundtrip_marker": True,
            "require_bind_kernel_agreement": True,
            "python_integration_files": ["tests/python/product/test_kernels.py"],
            "python_integration_markers": ["pytest.mark.l3", "pytest.mark.native", "roundtrip"],
            "c_integration_files": ["tests/c/test_luma_kv.c"],
            "c_integration_markers": ["L1", "L5", "encode", "decode"],
        }
    }
    assert int_gate.integration_violations(config, root=tmp_path) == []


def test_main_paths(monkeypatch: Any) -> None:
    """main covers skip / pass / fail."""
    monkeypatch.setattr(int_gate, "load_config", lambda: {"integration_standard": {"enable": False}})
    assert int_gate.main() == 0
    monkeypatch.setattr(int_gate, "load_config", lambda: {"integration_standard": {"enable": True}})
    monkeypatch.setattr(int_gate, "integration_violations", lambda _c: [])
    assert int_gate.main() == 0
    monkeypatch.setattr(
        int_gate,
        "integration_violations",
        lambda _c: [{"target": "t", "issue": "x", "current": "0", "limit": "1"}],
    )
    assert int_gate.main() == 1
