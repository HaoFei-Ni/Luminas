# LUM-RES-201 基准数据集说明

| 字段 | 内容 |
|:---|:---|
| 状态 | 计划 |
| 版本 | 0.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-res-skill` |
| 关联文档 | `LUM-RES-001` · `references/experiment-matrix.md` |

## 1. 范围（待撰写正文）

1. 官方数据集清单与固定协议：WikiText-2 test、C4 validation slice（hash 固定）、RULER + NIAH、MMLU 5-shot + 声明的 LongBench 子集。
2. 数据获取方式、版本与 hash 固定要求。
3. 与 `lumina/refs/` 的关系：原文入 refs；本文件只规定「使用哪份、如何用、门槛为何」。

## 2. 约束

- 禁止在数据集上 best-of-N；同 tokenizer、同 harness 方可比较。
- 须报告多个序列长度；禁止以单长度冒充长上下文结论。
