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
| `checks/robustness` | Robustness / fault-tolerance tests L5 |
| `checks/arch_compliance` | Architecture compliance tests L5 |
| `checks/endurance` | Endurance / fatigue tests L5 |
| `checks/integration` | End-to-end integration tests L5 |
| `checks/standards` | Shared L5 standard helpers |
| `reporting` | Python structure gate + bilingual Markdown/JSON |
| `support` | Cache layout, Hypothesis profiles, metrics facade |

## CLI

```bash
uv run python -m tools.run_quality_gate
uv run python -m tools.checks.arch_compliance.gate
uv run python -m tools.checks.endurance.gate
uv run python -m tools.checks.integration.gate
```

Authority: `../quality-gate.toml`. Artifacts: `../tests/reports/`.
