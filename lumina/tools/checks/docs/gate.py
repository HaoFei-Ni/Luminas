"""正式文档质量门禁（架构 / 技术 / 实验研究）.

真值源：``quality-gate.toml`` ``[document_standard]``；写作规则见 ``docs/README.md``。
经 ``run_quality_gate`` 调用。
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — Path used for exists/glob/read
from typing import Any

from tools.checks.docs.level import document_level_violations
from tools.checks.docs.meta import file_doc_violations
from tools.checks.docs.record import violation
from tools.support.gate_config import load_quality_gate as load_config

_DOMAIN_KEYS = ("architecture", "technical", "research")


def document_violations(config: dict[str, Any]) -> list[dict[str, str]]:
    """Collect L5 document-quality violations across configured domains."""
    standard = config.get("document_standard", {})
    if not standard.get("enable", False):
        return []
    out = document_level_violations(config)
    # 单遍三域：架构设计 / 技术 / 实验研究，避免漏扫某一类。
    for name in _DOMAIN_KEYS:
        domain = standard.get(name)
        if isinstance(domain, dict):
            out.extend(_domain_file_hits(domain, standard))
    return out


def _domain_file_hits(domain: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, str]]:
    """Scan one domain's include roots for matching formal Markdown files."""
    out: list[dict[str, str]] = []
    pattern = str(domain.get("file_glob", "LUM-*.md"))
    # 单遍根：每个 include_path 独立 glob，避免跨域路径串扰。
    for root in list(domain.get("include_paths") or []):
        out.extend(_root_file_hits(Path(root), pattern, domain, standard))
    return out


def _root_file_hits(
    root_path: Path,
    pattern: str,
    domain: dict[str, Any],
    standard: dict[str, Any],
) -> list[dict[str, str]]:
    """Scan a single include root; emit missing-dir or per-file findings."""
    if not root_path.is_dir():
        return [violation(root_path.as_posix(), "文档域 include_paths 目录不存在")]
    out: list[dict[str, str]] = []
    # 必须按 stem 排序：报告稳定，CI diff 可读。
    for path in sorted(root_path.glob(pattern), key=lambda p: p.name):
        out.extend(file_doc_violations(path, path.as_posix(), domain, standard))
    return out


def main() -> int:
    """CLI entry for the document-quality stage."""
    config = load_config()
    standard = config.get("document_standard", {})
    if not standard.get("enable", False):
        print("[INFO] document_standard 未启用，跳过文档质量门禁")
        return 0
    violations = document_violations(config)
    print(f"[INFO] docs-l5 findings={len(violations)}")
    # 单遍：逐条输出，避免汇总丢失定位。
    for item in violations:
        print(f"  - {item['target']}: {item['issue']}")
    if violations:
        print("[FAIL] docs-l5")
        return 1
    print("[PASS] docs-l5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
