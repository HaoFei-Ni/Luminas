# Luminas Official Experiment Matrix

Lock this suite in the lab log **before** the first official run. Replacing a dataset or baseline is allowed only if recorded first. Do not swap after seeing results.

GPU tiers (engineering support): **S = 4 GB / M = 24 GB / L = 80 GB**.

## Default datasets

| Purpose | Default | Protocol notes |
|---|---|---|
| Model-level PPL | WikiText-2 test | Same tokenizer and stride = 512 as the uncompressed baseline |
| Secondary PPL | C4 validation slice (hash-pinned file) | Optional; required before camera-ready |
| Long-context recall | RULER + needle-in-a-haystack | Official scripts; same needle policy across methods |
| Downstream | MMLU 5-shot + declared LongBench subset | Official harness; list LongBench tasks in the lab log |

## Sequence-length gradient (required)

| Length | GPU tier | Required |
|---|---|---|
| 4,096 | S / M / L | Yes |
| 32,768 | M / L | Yes |
| 131,072 | L | Yes when claiming “ultra-long context” |
| 524,288 | L multi-GPU or explicit opt-in | Optional |

Do not report a single length as the long-context result.

## Compression-ratio gradient (required)

Ratios are **KV bytes vs uncompressed FP16 KV** for the same sequence.

| Ratio | Intent |
|---|---|
| 2× | Mild; expected lossless if the method is real |
| 4× | Default operating point |
| 8× | Stress; may leave the lossless region — report the break point honestly |

Plot PPL, task score, tokens/s, and peak memory against ratio on one figure family.

## SOTA / class baselines (required)

Pick **at least three** methods from **at least two** classes. Run with published defaults unless a paper specifies a fair retune; retunes must apply to Luminas as well.

| Class | Default picks | Role |
|---|---|---|
| Uncompressed | Dense FP16 KV | Baseline control |
| Quantization | KIVI, KVQuant, or GPTQ/AWQ **as KV/weight baselines** | SOTA control — not Luminas impl |
| Eviction / sparse | H2O, SnapKV, StreamingLLM | SOTA control |
| Low-rank | One published low-rank KV method | SOTA control |
| Negative | Luminas minus the claimed novel module, **same param count** | Negative control |

Orchestra skills for GPTQ / AWQ / HQQ / pruning / FlashAttention may **set up** these baselines. They must not implement the Luminas path.

## Ablation matrix

One axis at a time. Every cell uses seeds `{0,1,2,3,4}`, same GPU tier, same eval harness.

| Cell | Change | Everything else |
|---|---|---|
| B0 | Uncompressed baseline | — |
| A1 | Add module 1 only | = B0 |
| A2 | Add module 2 only | = B0 |
| A12 | Modules 1+2 | = B0 |
| N1 | Remove module 1 from full system | = full |

Add rows for each claimed contribution. Do not skip the negative cell.

## Memory-tier check

| Tier | VRAM | Must show |
|---|---|---|
| S | **4 GB** | Runs at 4k; degrade path fires; L5 numeric still passes |
| M | 24 GB | 4k + 32k; no leak across 5 repeats |
| L | 80 GB | 128k enabled; compression still wins memory vs B0 |

Do not claim a continuous 4–120 GB sweep.

## Metrics that must appear together

Accuracy (PPL and/or task), throughput, peak memory, compute efficiency (FLOP/s or roofline fraction). Missing one of the four blocks a paper-facing claim.
