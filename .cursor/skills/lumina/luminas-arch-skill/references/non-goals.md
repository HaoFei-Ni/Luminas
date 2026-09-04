# Luminas Non-Goals

This file is the authoritative reject list. If a request matches a row, refuse the implementation path and point to the allowed alternative.

## Implementation paths that are out of scope

| Request looks like | Do not do | Do instead |
|---|---|---|
| Quantize KV or weights to 2/3/4/8-bit as the product path | Call GPTQ / AWQ / HQQ / bitsandbytes / KVQuant as the Luminas compressor | Treat those methods as **baselines only** in `research-skill` comparisons |
| Prune or sparsify weights to save KV | Wanda, SparseGPT, N:M structured prune as the cache solution | Keep sparsity as a **reference idea**; native kernels live under `lumina/` |
| Drop tokens / evict cache as "compression" | H2O, SnapKV, StreamingLLM as the Luminas mechanism | Allowed as **SOTA controls**, not as `luma_*` kernels |
| Low-rank KV approximation as the product path | Ship SVD / LoRA-on-KV as the compressor | Allowed as a **baseline class** |
| Patch upstream SpikingBrain / MoBA / FLA / vLLM in place | Edit `spb2/`, `spb2vl/`, `spb2_vllm/`, `MoBA/`, `flash-linear-attention_dev/` to "become Luminas" | Read-only study; re-implement needed ideas under `lumina/` |
| Vendor official Mamba / Falcon-H1 / Ouro checkpoints as the model | `from mamba_ssm import ...` as the architecture | Re-implement the adopted primitive in the kernel layer |
| FlashAttention as a substitute for the native attention/KV path | Make `flash-attn` the source of truth for Luminas attention | May be used as a **baseline kernel** or a temporary scaffolding, never as the lossless KV implementation |
| RoPE / YaRN / ALiBi context-extension as the long-context story | Claim long context is solved by position interpolation | Long context is a property of the native cache + hybrid attention design |
| Pure-PyTorch Ouro (or any looped) model as production | Put the compute body in Python | Loop **control** may live in the scheduler; the body calls `luma_*` / `luma_cuda_*` / `luma_triton_*` |
| Autoresearch pivot off the locked thesis | Change the research question to "whatever works" | Inner-loop experiments stay inside lossless KV + hybrid architecture |

## Claims that are out of scope

- Do not write "zero degradation", "bit-exact with FP16", or "lossless" unless the three-level gate in `research-skill` has been run and archived.
- Do not call Luminas a SpikingBrain2.0 fork, a quantization paper, or a FlashAttention wrapper.
- Do not target Nature as the only venue. Nature-style **reproducibility** (locked deps, seeds, hashes) is required; venue is chosen later.

## Allowed reference use

Reading papers and vendor code for Falcon-H1, Mamba-3, SpikingBrain2.0, Ouro, MoBA, SSE, FlashAttention is allowed. Copying their modules into `lumina/` is not. Terms keep the meaning from the source paper; implementations do not keep the source layout.
