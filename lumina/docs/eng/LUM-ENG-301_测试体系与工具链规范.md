# LUM-ENG-301 测试体系与工具链规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 草案 |
| 版本 | 0.3 |
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
| python-structure | `tools.reporting.python_gate` | Size / complexity / architecture / HA（`tools` + `tests`；不含 `theory/`） |
| c-structure | `tools.checks.native.gate` | C/CUDA structure + zero-loop hot path |
| naming-l5 | `tools.checks.naming.gate` | 文件命名质量 L5 |
| perf-l4 | `tools.checks.performance.gate` | 2+5 timed runs; ≤2% regression |
| docs-l5 | `tools.checks.docs.gate` | 架构/技术/实验研究文档质量 L5 |
| layout-l5 | `tools.checks.layout.gate` | 目录结构质量 L5 |
| robustness-l5 | `tools.checks.robustness.gate` | 鲁棒性与异常容错测试 L5 |
| arch-compliance-l5 | `tools.checks.arch_compliance.gate` | 架构合规性测试 L5 |
| endurance-l5 | `tools.checks.endurance.gate` | 长稳与疲劳测试 L5 |
| integration-l5 | `tools.checks.integration.gate` | 端到端集成测试 L5 |

Commit-time (seconds): root `.pre-commit-config.yaml` → ruff + `tools.complexity_precommit` only.

### 3.1 Report artifacts (`tests/reports/`)

| File | Consumers |
|---|---|
| `complexipy.json` | Gate input (raw feed) |
| `quality-gate.md` | Review / audit（中英双语） |
| `quality-gate.json` | CI parsers（`verdict`, `health_score`, `findings` + `issue_en`） |

### 3.2 Package layout

- `tools/checks/` — analyzers（… / docs / layout / robustness / arch_compliance / endurance / integration / standards）
- `tools/reporting/` — Python structure gate + bilingual report
- `tools/support/` — cache, Hypothesis, metrics facade
- `tests/python/{checks,support,product}/` — mirrors the above taxonomy

### 3.3 Python 覆盖率（分支 100%）

真值源：`pyproject.toml` `[tool.coverage]`。`branch = true`；`fail_under = 100`。

量测面（公共 API）：`tools.checks.docs` · `layout` · `naming.*` · `cognitive_level` · `robustness` · `arch_compliance` · `endurance` · `integration` · `standards` · `tools.support.metrics`。

```bash
uv run pytest tests/python/checks tests/python/support --cov --cov-report=term-missing
```
