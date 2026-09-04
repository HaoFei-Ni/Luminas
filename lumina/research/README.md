# lumina/research — 实验研究区

| 字段 | 内容 |
|:---|:---|
| 状态 | 规划中 |
| 权威技能 | `lumina-res-skill` |

标准与设计写在 `../docs/res/`；可复现产物归档在 `../experiments/`。本目录仅存放协议与官方案例的 **lab log**。

## 应收纳

- 套件锁定记录：数据集 / 基线 / hparams / GPU tier（S=4 / M=24 / L=80）/ seeds，首跑前冻结
- Phase 报告草稿（算子 → 模型 PPL → 任务）
- 消融 / SOTA 运行记录（结论数字以 `../experiments/EXP-*` 为准）

## 不应收纳

| 内容 | 去向 |
|---|---|
| 实验产物与提交物 | `../experiments/` |
| 论文排版 | `../paper/`（约定目录） |
| 方法推导 | `../theory/` |

## 规则摘要

- n = 5，seeds `{0,1,2,3,4}`，mean ± std，绑定 commit（`lumina-res-skill`）
- 未过三级门前写作 **candidate lossless path**（`LUM-RES-001`）
