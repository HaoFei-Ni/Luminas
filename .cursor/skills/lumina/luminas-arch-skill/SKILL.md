---
name: luminas-arch-skill
description: >-
  Defines Luminas architecture identity, four-layer stack, source isolation, and
  non-goals for an original lossless KV-cache compression system with hybrid
  attention and optional spiking-event kernels. Use when designing or changing
  model architecture, KV cache, attention, SSM, spiking or event-driven paths,
  directory layout, or deciding whether to reuse upstream SpikingBrain, Falcon-H1,
  Mamba, Ouro, FlashAttention, or quantization code. Triggers: Luminas, lumina/,
  lossless KV, KV cache, hybrid attention, spiking, 脉冲, Falcon-H1, Mamba-3, Ouro,
  architecture lock. Formerly spikingbrain-skill. Do not use for routine
  formatting, citation lookup, kernel style details, or implementing
  GPTQ/AWQ/HQQ/pruning as the product path.
metadata:
  version: "3.0.0"
  owner: luminas
  layer: architecture
---

# Luminas Architecture Lock

This skill owns identity, layering, source isolation, and Orchestra override. It does not own coding mechanics or experiment statistics.

## Priority

When skills disagree:

1. `luminas-arch-skill` — identity, non-goals, layers, source tree
2. `eng-standard-skill` — code, build, CI tests, GPU tiers
3. `research-skill` — experiments, **canonical lossless definition**, paper structure
4. Orchestra skills — tooling or baselines only

Read [references/non-goals.md](references/non-goals.md) before writing architecture or compression code. Read [references/orchestra-boundary.md](references/orchestra-boundary.md) before following any Orchestra domain skill.

## When to use

- New modules, operators, or cache designs
- User mentions lossless KV, hybrid attention, SSM, spiking / 脉冲, Falcon-H1, Mamba-3, Ouro
- Temptation to patch `spb2/`, `MoBA/`, `flash-linear-attention_dev/`, or to "just use" GPTQ / FlashAttention / official Mamba

## Do not use

- Formatting, commit-message-only, or citation fetch
- Kernel style, CMake, coverage numbers → `eng-standard-skill`
- Ablation matrices, p-values, paper sections → `research-skill`

## Identity

Luminas is an **original architecture project**. SpikingBrain2.0 in this repo is a **read-only technical base**, not a fork target.

- Core claim: a **new lossless KV-cache compression mechanism**, not quantization, pruning, eviction, or low-rank approximation.
- Hybrid capability may *reference* Falcon-H1 (attention–SSM mix, global attention as long-context recall backstop), Mamba-3 (linear-time sequence, hardware-aware scan), SpikingBrain2.0 (event-driven sparse compute, dual-path activation coding), and Ouro (looped depth vs parameter count). Terms keep the source-paper meaning.
- Implementations are native under `lumina/`. Do not import those projects as the Luminas model.

"Lossless" is **not** "zero degradation." A method is lossless only after it passes the three-level gate in `research-skill`. Until that gate is archived, say "candidate lossless path" and report numbers.

## Four layers

| Layer | Stack | May contain | Must not contain |
|---|---|---|---|
| Kernel | C99 CPU reference, CUDA C++, Triton | Numeric compute, tiling, memory movement | Python, serving, argument parsing |
| Binding | pybind11 | C-ABI marshal, dtype/shape checks, exception map, GIL release | Numeric algorithms |
| Scheduler | Python / PyTorch | Graph wiring, train/infer entry, eval harness, loop **control** (Ouro-style) | Operator math, KV encode/decode math |
| Infra (optional) | Rust | Serving runtime, distributed KV, admission, preprocess | Model numerics |

Pulse / event-driven paths belong in the **kernel** layer. Python only dispatches them.

## Source isolation

- Write original Luminas code under `lumina/` (create the tree if missing).
- Treat `spb2/`, `spb2vl/`, `spb2_vllm/`, `MoBA/`, `flash-linear-attention_dev/`, `run_model/` as **read-only references**.
- Do not patch upstream to "become" Luminas. Do not mix their symbols into `luma_*` libraries.

## Output bar

Ship research-prototype quality: native kernels or bindings, eval entry, locked config, commit-hash-tagged artifacts. No toy notebooks presented as the architecture. Venue is **not** locked to Nature; reproducibility rules still apply (locked deps, seeds, hashes) via `eng-standard-skill` and `research-skill`.

## Additional resources

- [references/non-goals.md](references/non-goals.md)
- [references/orchestra-boundary.md](references/orchestra-boundary.md)
