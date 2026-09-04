---
name: lumina-res-skill
description: >-
  Enforces Luminas experiment design, the canonical three-level lossless KV
  definition, ablation and SOTA matrices, and reproducibility rules for
  paper-grade results. Use when designing experiments, running ablations,
  claiming lossless or 无损 compression, reporting PPL, RULER, MMLU, or LongBench,
  or drafting paper sections. Triggers: ablation, PPL, lossless, 无损, 消融, 实验,
  论文. Do not use for kernel coding standards, CMake, coverage, or choosing
  GPTQ/AWQ/HQQ as the Luminas product path.
metadata:
  version: "3.1.0"
  owner: luminas
  domain: res
  doc_prefix: LUM-RES
---

# Luminas Research

Owns experiment design, the **only** definition of “lossless”, statistics, and paper skeleton.
Coding mechanics live in `lumina-eng-skill`. Architecture identity lives in `lumina-arc-skill`.

## Priority

1. `lumina-arc-skill` — do not change the thesis or implement forbidden paths
2. `lumina-eng-skill` — kernels must already pass L1/L5 before model-level runs
3. `lumina-res-skill` — this file
4. Orchestra (`ml-paper-writing`, `systems-paper-writing`, `academic-plotting`) — prose, citations, figures **after** this skeleton

Do not let `0-autoresearch-skill` pivot the question or replace `lumina/` with a generic `src/` / `experiments/` tree. Orchestra routing: `lumina-arc-skill` → [references/orchestra-boundary.md](../lumina-arc-skill/references/orchestra-boundary.md).

## When to use

Protocol design, official runs, claiming lossless, writing results or paper sections.

## Do not use

- Kernel style, coverage, CMake → `lumina-eng-skill`
- “Should we just quantize?” → reject via `lumina-arc-skill`

## Canonical lossless definition

A method may be called **无损 / lossless / 论文级无损** only if the three-level gate in [references/experiment-matrix.md](references/experiment-matrix.md) is satisfied. Until Level 1 is archived: **candidate lossless path**.

Do not write “zero degradation” or “bit-exact with the baseline network”.

### Bit-exact identity clause

When the product codec proves `D∘E = id` (element-wise bit-exact) **and** Level 1 is archived PASS:

- Any deterministic evaluation functional `f` that depends on the model only through KV tensors satisfies `f(D(E(K)), D(E(V))) = f(K, V)`.
- Levels 2 and 3 hold by this identity; empirical suites are for regression and disclosure (ratio / throughput), **not** to relax Level 1.
- Paper wording: **论文级无损（算子重构）**, with formula ID and EXP archive path.
- Non-bit-exact methods must still run Levels 2 and 3 on the locked suite.

### Level 1 — numeric

Same 2-ulp rule as engineering L5:

`|x - x64| ≤ 2 * 2^{-23} * max(1, |x64|)`

- No NaN / Inf
- ≥ 99.9% of finite elements pass
- Archived histogram of log-abs error

### Level 2 — model (PPL)

- Primary: WikiText-2 test, stride 512, identical harness and context as the uncompressed baseline
- `ΔPPL = mean(PPL_method) - mean(PPL_baseline)` over n = 5 seeds `{0,1,2,3,4}`
- Pass: `ΔPPL ≤ 0.01` **and** two-sided Wilcoxon signed-rank on paired per-document NLL gives `p > 0.05` **and** `|Cohen's d| < 0.2`

### Level 3 — task

- Core: MMLU 5-shot and the locked LongBench subset; long-context: RULER and NIAH at 4k and 32k (128k when claiming ultra-long)
- Pass: each core score drops by **≤ 1.0 percentage point** vs baseline **and** RULER/NIAH difference is non-significant (`p > 0.05`) with absolute drop ≤ 1.0 point

If any level fails, the paper must state where the lossless region ends (ratio or length).

## Statistics (single rule)

- **n = 5** independent runs, seeds **`{0,1,2,3,4}`**. Deterministic kernel benches: 5 timed repeats after 2 warmup (engineering L4).
- Report **mean ± std**. No best-of-N.
- Normality: Shapiro–Wilk. Variance: Levene. If both pass → Welch t-test; else Wilcoxon / Mann–Whitney.
- Claiming **A beats B**: `p < 0.05` **and** `|Cohen's d| ≥ 0.5`.
- Claiming **equivalence / lossless**: Level 2 / Level 3 rules above — not `p < 0.05` alone.

## Experiment design

1. **One variable per cell.** Same seeds, hparams, harness, GPU tier.
2. **Three controls:** uncompressed baseline; ≥ 3 SOTA methods from ≥ 2 classes; negative (novel module removed, equal param count). Defaults in [references/experiment-matrix.md](references/experiment-matrix.md).
3. **Phase order:** operator (must pass engineering L1/L5 and roofline ≥ 70% of the stated bound) → model PPL → task. Do not start Phase 2 if Phase 1 fails.
4. Operator complexity: measured FLOP and peak bytes within **5%** of the paper formula, or the formula is wrong.

## Execution order

1. Pilot on a slice (not reportable)
2. Lock the suite in the lab log
3. Phase 1 → 2 → 3 reports
4. Ablation matrix
5. SOTA table
6. Stats + failure cases
7. Claims that the numbers support

## Reproducibility

Disclose GPU model/count, driver, CUDA, compiler, OS, every hparam, dataset name/version/split/hash, seeds, commit. Bind every table to that commit. Keep failed runs. Figures: error bars, n, test name. Tables: three-line. Public one-command reproduce for camera-ready.

## Paper

Skeleton and venue routing: [references/paper-structure.md](references/paper-structure.md). Fill it before applying Orchestra writing skills. `academic-plotting` must keep error bars.

## Related documents

| Doc | Role |
|---|---|
| `lumina/docs/res/LUM-RES-001` | Research overview / lossless gate |
| `lumina/docs/res/LUM-RES-101` | Ablation design |
| `lumina/docs/res/LUM-RES-201` | Datasets |
| `lumina/docs/res/LUM-RES-301` | Paper structure entry |

## Additional resources

- [references/experiment-matrix.md](references/experiment-matrix.md)
- [references/paper-structure.md](references/paper-structure.md)
