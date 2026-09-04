# LUM-RES-001 科研实验总标准

- 状态：**骨架（待评审）**
- 关联：`research-skill`（SKILL.md + `references/experiment-matrix.md`）
- 对应 skill：`.cursor/skills/lumina/research-skill/SKILL.md`

## 无损的唯一定义

可称 **无损 / lossless** 仅当 `research-skill` 锁定的三级门槛全部通过（矩阵见 `references/experiment-matrix.md`）：

1. **Level 1 数值**：与 FP64 同 2-ulp 规则（`|x − x64| ≤ 2·2⁻²³·max(1,|x64|)`）；无 NaN/Inf；≥99.9% 有限元素通过；归档误差直方图。
2. **Level 2 模型（PPL）**：WikiText-2 test（stride 512，与未压缩基线同 harness）；n=5 seeds `{0,1,2,3,4}`；`ΔPPL ≤ 0.01` 且 Wilcoxon `p > 0.05` 且 `|Cohen's d| < 0.2`。
3. **Level 3 任务**：MMLU 5-shot + 锁定 LongBench 子集；长上下文 RULER/NIAH；核心分数下降 ≤ 1.0 百分点且差异不显著。

任一 level 失败 → 论文必须如实标注 lossless 区域的边界（比率或长度）。
未过门槛一律写 **candidate lossless path**。禁止写 "zero degradation / bit-exact with baseline"。

## 统计（唯一规则）

- n=5，seeds `{0,1,2,3,4}`；确定性 kernel bench：2 次 warmup + 5 次计时。
- 报 mean ± std，不报 best-of-N。
- 正态性 Shapiro–Wilk；方差 Levene；A 优于 B：`p<0.05` 且 `|d|≥0.5`；等价/无损按 Level 2/3 规则。

## 实验设计

1. 每格单变量；同 seeds/hparams/harness/GPU tier。
2. 三类对照：未压缩基线；≥3 个 SOTA（≥2 类）；负面（去掉声称的新模块，等参数量）。
3. 阶段顺序：算子（须先过工程 L1/L5 且 roofline ≥70%）→ 模型 PPL → 任务。Phase 1 不过不进入 Phase 2。

## 归档与复现

- 协议先锁进 lab log 再开跑；换数据集/基线必须先记录。
- 复现披露：GPU/驱动/CUDA/编译器/OS、全部 hparam、数据集名-版本-切分-hash、seeds、commit；每张表绑定 commit；保留失败 run。
- 产物归档规则见 `lumina/experiments/README.md`。
