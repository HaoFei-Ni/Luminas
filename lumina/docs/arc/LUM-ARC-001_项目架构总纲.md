# LUM-ARC-001 项目架构总纲

| 字段 | 内容 |
|:---|:---|
| 状态 | 草案 |
| 版本 | 1.2 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-arc-skill` |
| 关联文档 | `LUM-ARC-101` · `LUM-ARC-201` · `LUM-ARC-301` · `non-goals.md` |

## 1. 目的

规定 Luminas 的身份、源码隔离、分层原则与非目标摘要。派生 `LUM-ARC-*` 文档只扩展本总纲，不得另立身份或平行分层模型。

## 2. 身份

Luminas 为**原创架构项目**：目标是一套新的无损 KV-cache 压缩机制。产品路径不是量化、剪枝、驱逐或低秩近似。仓库内 SpikingBrain2.0 及相关上游树为**只读技术参考**，非 fork 目标。

## 3. 核心主张

1. **无损声明**：bit-exact 产品路径在 Level 1 归档 PASS 且适用恒等条款（`LUM-RES-001` §2.1）时可称 **论文级无损（算子重构）**；非 bit-exact 方法须实测三级门。未满足时写作 **candidate lossless path**，并报告实测数字。
2. **长上下文**：由原生 cache 与 hybrid attention 设计承载；不以 RoPE / YaRN / ALiBi 等位置插值作为长上下文故事的主结论。
3. **实现归属**：平台无关压缩数学不得进入 Python 或绑定层；原创实现仅落于 `lumina/`。

## 4. 分层总纲

职责视图（Kernel / Binding / Scheduler / Infra）与物理目录视图（`algorithm/` / `kernel/` / `wrapper/`）的唯一裁决点为 **LUM-ARC-101**。本总纲只锁定：

- `lumina/` 为唯一原创代码区；
- 两视图正交并存，禁止绕开裁决自定归属。

### 4.1 内容区四平面（目录心智模型）

在物理三层之上，用四平面组织 `lumina/` 顶层目录（**不改变** `algorithm/` / `kernel/` / `wrapper/` 冻结语义）：

| 平面 | 目录 | 说明 |
|---|---|---|
| Product | `algorithm/` · `kernel/` · `wrapper/` | 可交付算子栈（物理三层，锁定） |
| Engineering | `tools/` · `tests/` | 质量门禁与测试（见 `LUM-ENG-301`） |
| Knowledge | `docs/` · `theory/` · `refs/` | 正式规范、方法理论、外部文献 |
| Research ops | `research/` · `experiments/` | 协议 / lab log → `EXP-*` 归档 |

`.venv/`、`.cache/`、`build/` 等为产物，不列入架构平面。`theory/` 不并入 `research/`（避免与 F1–F7 / framework 权威路径漂移）。

## 5. 源码隔离

- 原创代码一律写入 `lumina/`。
- 下列路径为只读参考：`spb2/`、`spb2vl/`、`spb2_vllm/`、`MoBA/`、`flash-linear-attention_dev/`、`run_model/`。
- 禁止就地补丁上游以「成为 Luminas」；禁止将其符号混入 `luma_*` 库。
- 量化 / 驱逐 / 低秩等方法仅作实验对照（见 `LUM-RES-101`），不得作为产品路径。

## 6. 非目标（摘要）

完整拒绝清单见 `lumina-arc-skill/references/non-goals.md`。摘要：

- 不以 GPTQ / AWQ / HQQ / 剪枝 / 低秩作为产品压缩路径；
- 不以 `flash-attn` 或官方 Mamba 作为 Luminas 本体；
- 不以 “zero degradation” / “bit-exact with FP16” 作为无损结论用语。

## 7. 里程碑

版本与里程碑见 `lumina/docs/pm/LUM-PM-001`。
