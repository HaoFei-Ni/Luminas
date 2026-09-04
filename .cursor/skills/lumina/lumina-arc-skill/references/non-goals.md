# Luminas Non-Goals

Authoritative reject list for `lumina-arc-skill`. If a request matches a row, refuse that implementation path and point to the allowed alternative.

## Implementation paths that are out of scope

| Request looks like | Do not do | Do instead |
|---|---|---|
| Quantize KV or weights to 2/3/4/8-bit as the product path | Call GPTQ / AWQ / HQQ / bitsandbytes / KVQuant as the Luminas compressor | Treat those methods as **baselines only** in `lumina-res-skill` comparisons |
| Prune or sparsify weights to “save KV” | Wanda, SparseGPT, N:M structured prune as the cache solution | Keep sparsity as a **reference idea**; native kernels live under `lumina/` |
| Drop tokens / evict cache as “compression” | H2O, SnapKV, StreamingLLM as the Luminas mechanism | Allowed as **SOTA controls**, not as `luma_*` kernels |
| Low-rank KV approximation as the product path | Ship SVD / LoRA-on-KV as the compressor | Allowed as a **baseline class**; spectral theory in `theory/state-cache/` is not the product Enc/Dec |
| Patch upstream SpikingBrain / MoBA / FLA / vLLM in place | Edit `spb2/`, `spb2vl/`, `spb2_vllm/`, `MoBA/`, `flash-linear-attention_dev/` to “become Luminas” | Read-only study; re-implement needed ideas under `lumina/` |
| Vendor official Mamba / Falcon-H1 / Ouro as the model | `from mamba_ssm import …` as the architecture | Re-implement the adopted primitive in the kernel layer |
| FlashAttention as a substitute for the native attention/KV path | Make `flash-attn` the source of truth for Luminas attention | May be a **baseline kernel** or temporary scaffolding — never the lossless KV implementation |
| RoPE / YaRN / ALiBi as the long-context story | Claim long context is solved by position interpolation | Long context is a property of the native cache + hybrid attention design |
| Pure-PyTorch looped model as production | Put the compute body in Python | Loop **control** may live in the scheduler; the body calls `luma_*` / `luma_cuda_*` / `luma_triton_*` |
| Autoresearch pivot off the locked thesis | Change the research question to “whatever works” | Inner-loop experiments stay inside lossless KV + hybrid architecture |

## Claims that are out of scope

- Do not write “zero degradation”, “bit-exact with FP16”, or “lossless” unless the three-level gate in `lumina-res-skill` has been run and archived.
- Do not call Luminas a SpikingBrain2.0 fork, a quantization paper, or a FlashAttention wrapper.
- Do not treat theory F1–F7 (spectral collapse) as a product lossless claim.
- Do not target Nature as the only venue. Nature-style **reproducibility** (locked deps, seeds, hashes) is required; venue is chosen later.

## Allowed reference use

Reading papers and vendor code for Falcon-H1, Mamba-3, SpikingBrain2.0, Ouro, MoBA, SSE, FlashAttention is allowed. Copying their modules into `lumina/` is not. Terms keep the meaning from the source paper; implementations do not keep the source layout.
