# LUM-RES-101 消融实验设计方案

- 状态：**计划（尚未撰写）**
- 关联：`LUM-RES-001` · `research-skill`（Experiment design / Ablation）

## 计划覆盖内容

- 消融矩阵模板（每格单变量；A1/A2/A12/N1 负面格）
- SOTA / 类基线选择规则（≥3 方法、≥2 类，官方默认参数）
- 压缩比梯度（2×/4×/8×）与序列长度梯度（4k/32k/128k/524k）的强制报告
- 必同现指标：accuracy、throughput、peak memory、compute efficiency

## 执行准绳

默认数据集、基线类、矩阵行全部以 `references/experiment-matrix.md` 为准，本文件不另造一套。
