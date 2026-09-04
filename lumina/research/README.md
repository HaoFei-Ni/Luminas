# lumina/research — 实验研究区（规划中）

> research-skill 约定：协议与官方案例的 **lab log** 放这里；标准只写在 `../docs/res/`；产物只归档到 `../experiments/`。

## 应放入本目录的内容

- 实验协议锁定记录（lab log）：数据集/基线/hparams/GPU tier/seeds 在首跑前冻结
- 三段式（算子 → 模型 PPL → 任务）的 Phase 报告草稿
- 消融 / SOTA 对照运行记录（结论与数字以 `../experiments/EXP-*` 归档为准）

## 不应放入

- 实验产物数据与提交物 → `../experiments/`（同属 `lumina/`）
- 论文排版 → `../paper/`（research-skill 约定，待建）
- 方法推导 → `../theory/`

## 参考规则

- n=5、seeds `{0,1,2,3,4}`、mean±std、绑定 commit（`research-skill`）
- 未过三级门槛前称 candidate lossless path（`LUM-RES-001`）
