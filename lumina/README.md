# lumina/ — Luminas 唯一内容区

源码、正式文档与实验归档均收纳于此。分层裁决：[`docs/arc/LUM-ARC-101`](docs/arc/LUM-ARC-101_核心分层架构设计.md)。仓库导航：根目录 [`README.md`](../README.md)。

## 内容区四平面

| 平面 | 目录 | 职责 | 状态 |
|---|---|---|---|
| **Product**（冻结） | `algorithm/` → `kernel/` → `wrapper/` | 可交付算子栈（物理三层，CMake superproject） | **候选 ABI**：Enc/Dec 仍为恒等占位，未过三级门前禁止称「无损」 |
| **Engineering** | `tools/` · `tests/` | 质量门禁 + C/Python 测试 | 已启用 |
| **Knowledge** | `docs/` · `theory/` · `refs/` | LUM-* 规范、表征坍缩理论、外部文献 | 草案 / 启用并存 |
| **Research ops** | `research/` → `experiments/` | 实验协议 / lab log → `EXP-*` 归档 | 骨架 |

**不进架构叙事（产物）**：`.venv/`、`.cache/`、`build/`、`__pycache__/`（gitignore）。

`theory/` 保持独立（方法数学 / F1–F7），**不**并入 `research/`。

## 产品物理三层（锁定）

| 目录 | 职责 |
|---|---|
| `algorithm/` | 平台无关 ANSI C 压缩 / 解压数学 |
| `kernel/` | C-ABI 头、CUDA / CPU 算子、有损基线 |
| `wrapper/` | 对外 API / pybind 封装 |

禁止改名或塞入 `src/`；与职责四层的裁决见 `LUM-ARC-101`。

## 产品成熟度（诚实口径）

- 产品扩展：`_luma_native` → 仅 `luma_kv_encode` / `luma_kv_decode`（**candidate**，恒等占位）。
- 有损基线扩展：`_luma_baseline` / `_luma_cuda` → quant / SVD / int8；**不是**产品无损路径。
- 算子与接口合同：`docs/arc/LUM-ARC-201` · `LUM-ARC-301`。
- 称「无损」须通过 `lumina-res-skill` 三级门并归档；此前一律 **candidate lossless path**。

## Engineering 入口

```bash
# cwd = lumina/
uv run python -m tools.run_quality_gate
uv run pytest
cmake -S . -B ../outputs/build/lumina && cmake --build ../outputs/build/lumina
```

- 门禁包布局：[`tools/README.md`](tools/README.md)（`checks/` · `reporting/` · `support/`）
- 测试树：[`tests/README.md`](tests/README.md)（`c/` · `python/{checks,support,product}/` · `reports/`）

## 分层模型

| 视图 | 权威 | 内容 |
|---|---|---|
| 职责四层 | `lumina-arc-skill` | Kernel → Binding → Scheduler → Infra |
| 物理三层 | `lumina-eng-skill` | `algorithm/` → `kernel/` → `wrapper/` |
| 内容区四平面 | `LUM-ARC-001` §4.1 | Product · Engineering · Knowledge · Research ops |

**归属口径以 `docs/arc/LUM-ARC-101` 为唯一裁决点（职责 × 物理）。**

## 迁移记录（摘要）

Phase A/B/C（2026-09）已完成：算法 / 绑定迁出、头拆分、命名规范化、superproject 三层目标链。统一构建入口：`lumina/CMakeLists.txt`。细节见 `docs/arc/LUM-ARC-101`。
