# LUM-RES-201 基准数据集说明

- 状态：**计划（尚未撰写）**
- 关联：`LUM-RES-001` · `research-skill`（`references/experiment-matrix.md` 的 datasets/length/ratio 段）

## 计划覆盖内容

- 官方数据集清单与固定协议：WikiText-2 test、C4 validation slice（hash 固定）、RULER + NIAH、MMLU 5-shot + 声明 LongBench 子集
- 数据获取方式、版本与 hash 固定要求
- 与 `refs/` 的关系：论文与规范原文入 `lumina/refs/`，本文件只写"Luminas 用哪个、怎么用、门槛是什么"

## 约束

- 不在数据集上做 best-of-N；同 tokenizer/同 harness 才可比。
- 报告多个长度，禁止单长度冒充长上下文结论。
