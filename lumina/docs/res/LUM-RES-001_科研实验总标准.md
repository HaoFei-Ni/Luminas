# LUM-RES-001 科研实验总标准

| 字段 | 内容 |
|:---|:---|
| 状态 | 生效 |
| 版本 | 1.2 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-res-skill` |
| 关联文档 | `LUM-RES-101` · `LUM-RES-201` · `LUM-RES-301` · `references/experiment-matrix.md` |

## 1. 目的

规定官方实验的无损定义、统计规则与阶段顺序。套件细节以 `lumina-res-skill/references/experiment-matrix.md` 为准。

## 2. 无损的唯一定义

可称为 **无损 / lossless / 论文级无损**，当且仅当下列三级门槛满足（锁定套件见 `experiment-matrix.md`）：

| Level | 内容 | 通过条件（摘要） |
|---|---|---|
| 1 数值 | 相对 FP64 的 2-ulp 门 | 无 NaN/Inf；≥ 99.9% 有限元通过；归档误差直方图 |
| 2 模型 | WikiText-2 test，stride 512，与未压缩基线同 harness | n = 5，seeds `{0,1,2,3,4}`；`ΔPPL ≤ 0.01` 且 Wilcoxon `p > 0.05` 且 `|d| < 0.2` |
| 3 任务 | MMLU 5-shot + 锁定 LongBench；长上下文 RULER / NIAH | 核心分数下降 ≤ 1.0 百分点且差异不显著（`p > 0.05`） |

### 2.1 Bit-exact 恒等条款（产品 Enc/Dec）

当产品路径在论域上证明 `D∘E = id`（逐元 bit-exact，且 Level 1 已归档 PASS）时：

- 任意仅经 KV 张量读写的确定性评测泛函 `f` 满足 `f(D(E(K)), D(E(V))) = f(K, V)`。
- Level 2 / 3 **由恒等引理成立**；经验套件用于防回归与披露吞吐 / 压缩比，**不得**用来放宽 Level 1。
- 论文可称 **论文级无损（算子重构）**；归档入口：`experiments/EXP-001_kv-rle-bitexact/`。
- 禁止写作 “zero degradation” / “bit-exact with baseline network” 等模糊口号；须写清公式 ID（现行 `KV-ENC-CANDIDATE-1`）与 L1 归档路径。

非 bit-exact 方法仍须按上表实测 Level 2 / 3。任一实测 Level 失败：论文须标明 lossless 区域边界（比率或长度）。未满足 Level 1 或无法证明恒等时，一律写作 **candidate lossless path**。

## 3. 统计（唯一规则）

- n = 5，seeds `{0,1,2,3,4}`；确定性 kernel bench：2 次 warmup + 5 次计时（工程 L4）。
- 报告 mean ± std；禁止 best-of-N。
- 正态性 Shapiro–Wilk；方差 Levene；宣称 A 优于 B：`p < 0.05` 且 `|d| ≥ 0.5`；等价 / 无损按 Level 2 / 3。

## 4. 实验设计

1. 每格单变量；同 seeds、hparams、harness、GPU tier（S = 4 / M = 24 / L = 80 GB）。
2. 三类对照：未压缩基线；≥ 3 个 SOTA（≥ 2 类）；负面对照（去除声称新模块，等参数量）。
3. 阶段顺序：算子（须先过工程 L1/L5 且 roofline ≥ 70%）→ 模型 PPL → 任务。Phase 1 未通过不得进入 Phase 2。

## 5. 归档与复现

- 协议先写入 lab log 再开跑；更换数据集或基线须事先记录。
- 披露：GPU / 驱动 / CUDA / 编译器 / OS、全部 hparam、数据集名-版本-切分-hash、seeds、commit；每张表绑定 commit；保留失败 run。
- 产物归档见 `lumina/experiments/README.md`。
