# Luminas Paper Structure

Use this file when drafting sections. Load `ml-paper-writing` (NeurIPS / ICML / ICLR / ACL) or `systems-paper-writing` (OSDI / SOSP / ASPLOS / NSDI) **after** this skeleton is filled. Those skills must not drop lossless tables, error bars, or the three-level gate.

Target venue is **not** locked. Nature-style reproducibility (locked env, seeds, hashes, public scripts) is required regardless of venue.

## Abstract

Must include: problem, failure of lossy KV methods, method name, **lossless-gate numbers**, compression ratio and throughput / memory, one-sentence limitation. Reject drafts with no numbers.

## Introduction

1. KV-cache bottleneck at 32k–128k
2. Why quantization / eviction / low-rank lose accuracy
3. Three or four contributions, each mapped to a later table or figure
4. Roadmap paragraph

## Related Work

Group by route: quantization, eviction/sparsity, low-rank, architectural KV, hybrid attention / SSM, spiking / event-driven. Each group: idea, limit, difference from Luminas. No uncited comparison.

## Method

1. Block diagram of the four layers
2. Algorithm + error bound (why 2 ulp / why PPL should not move)
3. Complexity: time and KV bytes vs sequence length
4. Implementation: tiling, memory pool, degrade path

## Experimental Setup

Copy the locked suite from [experiment-matrix.md](experiment-matrix.md). Disclose GPU, driver, CUDA, compiler, seeds `{0,1,2,3,4}`, commit hash.

## Results

Order: operator → model (PPL) → task. Include the three-level lossless table, ablation matrix, SOTA table, length and ratio curves. Every mean has ± std and n=5.

## Discussion

Mechanistic reading, **failure cases**, sequences or ratios that leave the lossless region, what the negative control showed.

## Conclusion

Restate supported claims only. No new numbers.

## Appendix

Extra lengths, extra models, proofs, one-command reproduce script, code URL.
