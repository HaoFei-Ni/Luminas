# LUM-ARC-201 KV 压缩核心算子设计

| 字段 | 内容 |
|:---|:---|
| 状态 | 计划 |
| 版本 | 0.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-arc-skill`（身份）→ `lumina-eng-skill`（实现与测试） |
| 关联文档 | `LUM-ARC-001` · `LUM-ARC-101` · `LUM-ENG-301` · `LUM-RES-001` |

## 1. 范围（待撰写正文）

1. 无损 KV 压缩 / 解压核心算子的候选路径与设计约束。
2. 与 `lumina/theory/state-cache/` 的对应关系：表征坍缩框架（`framework.tex`，判据 F1–F7）提供谱秩侧闭合理论；**不等于**产品无损路径（见 `non-goals.md`）。
3. 算子复杂度的公式化声明（FLOP、峰值字节），供工程 L4 与实验 Phase 1 校验。

## 2. 撰写前必读

1. `lumina-arc-skill/references/non-goals.md`（禁止以量化 / 驱逐 / 低秩为产品路径）
2. `lumina-res-skill` 三级无损门定义
3. `lumina/theory/state-cache/framework.tex` 与 `verify/verify-degeneration.py`（F1–F7）

## 3. 约束

- 不在本文件重新定义分层（见 `LUM-ARC-101`）。
- 不因理论 F 门通过而宣称产品「无损 KV」。
