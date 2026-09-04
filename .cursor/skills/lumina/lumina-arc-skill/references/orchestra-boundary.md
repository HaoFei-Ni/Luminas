# Orchestra Skill Boundary

Luminas project skills outrank Orchestra domain skills on architecture, compression, kernels, and experiment gates. Orchestra skills remain usable as **tooling** or **baseline literature**, not as the implementation recipe.

## Priority

1. `lumina-arc-skill` — identity, non-goals, layering, source tree, Orchestra override
2. `lumina-eng-skill` — coding, build, CI-grade tests, GPU memory tiers (S = 4 / M = 24 / L = 80 GB)
3. `lumina-res-skill` — experiment design, canonical lossless definition, statistics, paper structure
4. Orchestra skills — only after 1–3 are satisfied

## Routing table

| Orchestra skill | Allowed use | Forbidden use |
|---|---|---|
| `gptq`, `awq-quantization`, `hqq-quantization`, `model-pruning` | Name them as SOTA / class baselines in an experiment protocol | Implement Luminas compression this way; “deploy 4-bit KV” as the product path |
| `mamba-architecture` | Read SSM / scan vocabulary and complexity claims | Import `mamba_ssm` or copy official Mamba as `lumina/` |
| `long-context` | Literature on RoPE / YaRN / ALiBi when writing Related Work | Solve Luminas long context by position-interpolation fine-tunes |
| `optimizing-attention-flash` / `flash-attention` | Baseline attention kernel; nsys comparison | Replace native lossless KV with FlashAttention memory tricks |
| `llama-cpp` | C kernel craft reference (prefix, memory, tests) | Copy llama.cpp files or adopt its API as Luminas |
| `ml-paper-writing` | NeurIPS / ICML / ICLR prose, citation verification, LaTeX | Override `lumina-res-skill` section order or lossless reporting |
| `systems-paper-writing` | OSDI / SOSP / ASPLOS page budget after venue is chosen | Rewrite the research question as a generic systems paper |
| `academic-plotting` | Figures; must include error bars and n | Drop error bars or cherry-pick a single run |
| `0-autoresearch-skill` / `autoresearch` | Inner-loop bookkeeping **inside** the locked thesis | Create a parallel `src/` `experiments/` tree that replaces `lumina/`; pivot the thesis; skip the three-level lossless gate |
| `ara-research-manager`, `ara-rigor-reviewer`, `compiler` | Post-task provenance and epistemic review | Drive kernel or architecture choices |
| `brainstorming-research-ideas`, `creative-thinking-for-research` | Ideation **explicitly requested** by the user | Quietly replace lossless KV with a new topic |

## Workspace layout vs autoresearch

Do not initialize the Orchestra default tree (`src/`, `experiments/{slug}/`, `paper/`) as a replacement for Luminas. If autoresearch bookkeeping is needed, keep it under `lumina/research/` (or a path the user names) and leave upstream SpikingBrain trees untouched.
