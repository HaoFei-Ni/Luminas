# lumina/tools — quality-gate package

Industry-style layout: **checks** (analyzers), **reporting** (verdicts), **support** (shared).

## Package map

| Package | Role |
|---|---|
| `checks/architecture` | Import graph, cycles, fan-out, inheritance, clones |
| `checks/native` | C/CUDA structure, hot-path loops, docs |
| `checks/reliability` | Unchecked exceptions, globals, None-risk |
| `checks/naming` | LUM-ENG-101 identifiers and filenames |
| `checks/performance` | L4 timing protocol and regression gate |
| `checks/python` | Python AST size / structure / recursion |
| `checks/comments` | Why-comment policy for complex statements |
| `checks/docs` | Formal Markdown L5 (arc / eng / res) |
| `checks/layout` | Directory structure L5 (ARC-101 layers + planes) |
| `reporting` | Python structure gate + bilingual Markdown/JSON |
| `support` | Cache layout, Hypothesis profiles, metrics facade |

## CLI

```bash
uv run python -m tools.run_quality_gate
uv run python -m tools.complexity_precommit
uv run python -m tools.reporting.python_gate
uv run python -m tools.checks.native.gate
uv run python -m tools.checks.naming.gate
uv run python -m tools.checks.performance.gate
uv run python -m tools.checks.docs.gate
uv run python -m tools.checks.layout.gate
```

Authority: `../quality-gate.toml`. Artifacts: `../tests/reports/`.
