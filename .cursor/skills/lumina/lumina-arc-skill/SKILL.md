---
name: lumina-arc-skill
description: >-
  Defines Luminas architecture identity, duty-layer stack, source isolation, and
  non-goals for an original lossless KV-cache compression system with hybrid
  attention and optional spiking-event kernels. Use when designing or changing
  model architecture, KV cache, attention, SSM, spiking or event-driven paths,
  directory layout, or deciding whether to reuse upstream SpikingBrain, Falcon-H1,
  Mamba, Ouro, FlashAttention, or quantization code. Triggers: Luminas, lumina/,
  lossless KV, KV cache, hybrid attention, spiking, 脉冲, Falcon-H1, Mamba-3, Ouro,
  architecture lock. Do not use for routine formatting, citation lookup, kernel
  style, CMake, coverage, or implementing GPTQ/AWQ/HQQ/pruning as the product path.
metadata:
  version: "3.1.0"
  owner: luminas
  domain: arc
  doc_prefix: LUM-ARC
---

# Luminas Architecture

Owns identity, non-goals, duty layers, source isolation, and Orchestra override.
Does not own coding mechanics (`lumina-eng-skill`) or experiment statistics (`lumina-res-skill`).

## Priority

1. `lumina-arc-skill` — identity, non-goals, layers, source tree
2. `lumina-eng-skill` — code, build, CI tests, GPU tiers
3. `lumina-res-skill` — experiments, canonical lossless definition, paper structure
4. Orchestra — tooling or baselines only

Before architecture or compression work, read [references/non-goals.md](references/non-goals.md).
Before following any Orchestra domain skill, read [references/orchestra-boundary.md](references/orchestra-boundary.md).

## When to use

- New modules, operators, or cache designs
- Mentions of lossless KV, hybrid attention, SSM, spiking / 脉冲, Falcon-H1, Mamba-3, Ouro
- Temptation to patch `spb2/`, `MoBA/`, `flash-linear-attention_dev/`, or to ship GPTQ / FlashAttention / official Mamba as the product path

## Do not use

- Formatting or commit-message-only tasks
- Kernel style, CMake, coverage → `lumina-eng-skill`
- Ablation matrices, p-values, paper sections → `lumina-res-skill`

## Identity

Luminas is an **original architecture project**. SpikingBrain2.0 trees in this repo are a **read-only technical base**, not a fork target.

- **Core claim:** a new lossless KV-cache compression mechanism — not quantization, pruning, eviction, or low-rank approximation as the product path.
- **Hybrid references (vocabulary only):** Falcon-H1 (attention–SSM mix; global attention as long-context recall backstop), Mamba-3 (linear-time sequence; hardware-aware scan), SpikingBrain2.0 (event-driven sparse compute; dual-path activation coding), Ouro (looped depth vs parameter count). Terms keep the source-paper meaning.
- **Implementation:** native code under `lumina/` only. Do not import those projects as the Luminas model.

“Lossless” is not “zero degradation.” A method is lossless only after the three-level gate in `lumina-res-skill` is archived. Until then: **candidate lossless path**, with real numbers.

## Duty layers

Runtime roles (orthogonal to the physical `algorithm/` / `kernel/` / `wrapper/` tree owned by `lumina-eng-skill`). Adjudication: `LUM-ARC-101`.

| Layer | Stack | May contain | Must not contain |
|---|---|---|---|
| Kernel | C99 CPU reference, CUDA C++, Triton | Numeric compute, tiling, memory movement | Python, serving, argument parsing |
| Binding | pybind11 | C-ABI marshal, dtype/shape checks, exception map, GIL release | Numeric algorithms |
| Scheduler | Python / PyTorch | Graph wiring, train/infer entry, eval harness, loop **control** (Ouro-style) | Operator math, KV encode/decode math |
| Infra (optional) | Rust | Serving runtime, distributed KV, admission, preprocess | Model numerics |

Pulse / event-driven paths belong in the **Kernel** layer. Python only dispatches them.

## Source isolation

- Write original Luminas code under `lumina/` (create the tree if missing).
- Treat `spb2/`, `spb2vl/`, `spb2_vllm/`, `MoBA/`, `flash-linear-attention_dev/`, `run_model/` as **read-only references**.
- Do not patch upstream to “become” Luminas. Do not mix their symbols into `luma_*` libraries.

## Output bar

Ship research-prototype quality: native kernels or bindings, eval entry, locked config, commit-hash-tagged artifacts. No toy notebooks as the architecture. Venue is not locked to Nature; reproducibility (locked deps, seeds, hashes) still applies via `lumina-eng-skill` and `lumina-res-skill`.

## Related documents

| Doc | Role |
|---|---|
| `lumina/docs/arc/LUM-ARC-001` | Architecture overview |
| `lumina/docs/arc/LUM-ARC-101` | Layering adjudication (duty vs physical) |
| `lumina/docs/arc/LUM-ARC-201` | KV operator design |
| `lumina/docs/arc/LUM-ARC-301` | Inter-layer interfaces |

## Additional resources

- [references/non-goals.md](references/non-goals.md)
- [references/orchestra-boundary.md](references/orchestra-boundary.md)
