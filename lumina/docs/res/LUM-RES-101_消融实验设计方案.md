# LUM-RES-101 消融实验设计方案

| 字段 | 内容 |
|:---|:---|
| 状态 | 计划 |
| 版本 | 0.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-res-skill` |
| 关联文档 | `LUM-RES-001` · `references/experiment-matrix.md` |

## 1. 范围（待撰写正文）

1. 消融矩阵模板（每格单变量；A1 / A2 / A12 / N1 负面格）。
2. SOTA / 类基线选择规则（≥ 3 方法、≥ 2 类；官方默认参数）。
3. 压缩比梯度（2× / 4× / 8×）与序列长度梯度（4k / 32k / 128k / 524k）的强制报告。
4. 同图族必现指标：accuracy、throughput、peak memory、compute efficiency。

## 2. 执行准绳

默认数据集、基线类与矩阵行以 `references/experiment-matrix.md` 为准；本文件不另立平行矩阵。
