# tests/reports/

Quality-gate artifacts under `lumina/` (generated; gitignored). Authority: `quality-gate.toml` `[report]`.

| Artifact | Role | Producer |
|---|---|---|
| `complexipy.json` | Raw cognitive-complexity feed | `complexipy` via `tools.run_quality_gate` |
| `quality-gate.md` | Human verdict report（中英双语，schema `1.1`） | `tools.reporting.report` |
| `quality-gate.json` | Machine-readable summary for CI（`locale=zh-CN/en`；keys 英文） | `tools.reporting.report` |

## How to regenerate

From `lumina/`:

```bash
uv run python -m tools.run_quality_gate
```

Or Python structure only (requires an existing `complexipy.json`):

```bash
uv run complexipy --output-format=json --output=tests/reports/complexipy.json --failed=false --quiet=true tools tests
uv run python -m tools.reporting.python_gate
```

## Schema notes

- `quality-gate.json` fields: `schema_version`, `locale` (`zh-CN/en`), `verdict` (`PASS`/`FAIL`), `health_score`, `grade`, `metrics`, `thresholds`, `findings`（含 `issue` + `issue_en`）。
- Markdown 为人读中英双语；JSON 键名保持英文便于 CI 解析。
- Thresholds live only in `quality-gate.toml`; do not hard-code limits in application code.
- `pyproject.toml` `[tool.complexipy].output` must mirror `[report].json_report_path`.
- Scan scope is `tools` + `tests` only; `theory/` is the F1–F7 track and is not under product structure thresholds.
