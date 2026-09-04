# EXP-001 — Bit-exact KV RLE 无损归档

| 字段 | 内容 |
|:---|:---|
| 状态 | 进行中（Level 1 PASS） |
| 日期 | 2026-09-05 |
| 方法 | `KV-ENC-CANDIDATE-1` 精确 f32 游程编码 |
| commit | （合并后回填） |
| 权威 | `lumina-res-skill` 三级门 · `LUM-ARC-201` · `LUM-RES-001` §2.1 |

## 1. 锁定声明

本 EXP 锁定：产品 Enc/Dec 为 **bit-exact** 浮点重构（非量化 / 非驱逐 / 非低秩）。

| 级别 | 主张 | 本 EXP 处置 |
|---|---|---|
| L1 数值 | ≥99.9% 元素过 2-ulp；无 NaN/Inf；归档 log-abs 直方图 | `verify_l1_archive.py` |
| L2 模型 | ΔPPL≤0.01 等 | **恒等引理**：bit-exact 重构 ⇒ 任意确定性 `f(K,V)` 不变；全量 WikiText-2 在模型接入后补跑并回填 |
| L3 任务 | ≤1pp 等 | 同上恒等引理；全量 MMLU/LongBench/RULER 模型接入后补跑 |

论文可称「KV 张量重构无损 / lossless reconstruction」。完整端到端套件数字在模型 harness 接入后写入本目录 `results/`。

## 2. 运行

```powershell
cd lumina
uv run python -m tools.run_build --test
uv run python ../experiments/EXP-001_kv-rle-bitexact/verify_l1_archive.py
```

产物：`artifacts/l1_error_hist.json`（gitignore 可选；提交摘要表）。

## 3. 恒等引理（L2/L3）

设 `D∘E` 对论域 `X`（全体有限 f32 向量）满足 `D(E(x))=x`（逐元 bit-exact）。  
对任意确定性评测泛函 `f`（PPL、准确率等）若仅通过 KV 张量依赖模型状态，则：

`f(D(E(K)), D(E(V))) = f(K, V)`。

因此在「评测只经产品 Enc/Dec 读写 KV」的前提下，L2/L3 与未压缩基线 **数值同分布**；经验套件用于防回归与披露压缩比/吞吐，而非放宽无损定义。
