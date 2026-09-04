# LUM-ENG-301 测试体系与工具链规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 草案 |
| 版本 | 0.2 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-eng-skill`（Tests） |
| 关联文档 | `LUM-ENG-001` · `references/test-matrix.md` · `quality-gate.toml` |

## 1. 范围

1. 产品 L1–L5 的落地方式、覆盖率测量与门槛。
2. 理论 F1–F7（`theory/state-cache/verify/verify-degeneration.py`：E / MC / DATA）与产品轨道的边界。
3. 工具链：pytest + xdist + Hypothesis；mypy + ruff；nsys / ncu / torch.profiler；compute-sanitizer；pytest-benchmark。
4. 质量门禁编排与报告制品（见 §3）。
5. CI 命令约定；工程 / 理论绿灯**不授予**论文 lossless 声明。

## 2. 执行准绳

`lumina-eng-skill/references/test-matrix.md` 为唯一执行细节来源。本文档仅作入口与决策记录。

GPU 档位：**S = 4 GB / M = 24 GB / L = 80 GB**。

## 3. 质量门禁（Quality Gate）

真值源：`lumina/quality-gate.toml`。编排入口（cwd = `lumina/`）：

```bash
uv run python -m tools.run_quality_gate
```

| Stage | Module | Role |
|---|---|---|
| ruff | `ruff check tools tests` | Lint + docstring D |
| python-structure | `tools.ci_quality_gate` | Size / complexity / architecture / HA（`tools` + `tests`；不含 `theory/`） |
| c-structure | `tools.c_quality_gate` | C/CUDA structure + zero-loop hot path |
| naming | `tools.naming_gate` | LUM-ENG-101 |
| perf-l4 | `tools.perf_gate` | 2+5 timed runs; ≤2% regression |

Commit-time (seconds): root `.pre-commit-config.yaml` → ruff + `tools.complexity_precommit` only.

### 3.1 Report artifacts (`tests/reports/`)

| File | Consumers |
|---|---|
| `complexipy.json` | Gate input (raw feed) |
| `quality-gate.md` | Review / audit（中英双语） |
| `quality-gate.json` | CI parsers（`verdict`, `health_score`, `findings` + `issue_en`） |

Details: `tests/reports/README.md`. Do not commit generated reports.
