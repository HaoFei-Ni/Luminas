---
name: eng-standard-skill
description: >-
  Enforces Luminas coding, build, and CI test standards for C99, CUDA, Triton,
  Rust, Python, and pybind11, including luma_ prefixes, numerical 2-ulp checks,
  and discrete GPU memory tiers (8/24/80 GB). Use when writing or reviewing
  kernels, bindings, CMake, tests, or benchmarks, or when the user mentions
  CUDA, Triton, kernel, 算子, nsys, ncu, coverage, pybind11, or luma_ prefixes.
  Do not use for paper structure, ablation design, architecture identity, or
  claiming lossless from unit tests alone.
paths:
  - "lumina/**"
  - "**/*.{c,h,cu,cuh}"
metadata:
  version: "3.0.0"
  owner: luminas
  layer: engineering
---

# Luminas Engineering Standard

This skill owns code, build, and **CI-grade** tests. It does not redefine "lossless" and does not own paper experiments.

## Priority

1. `luminas-arch-skill` — identity and non-goals (do not implement GPTQ/AWQ/pruning; do not patch upstream)
2. `eng-standard-skill` — this file
3. `research-skill` — PPL / task / statistics / paper
4. Orchestra — baselines and tools only

Test tables and commands: [references/test-matrix.md](references/test-matrix.md).

## When to use

Writing or reviewing anything under `lumina/` in C, CUDA, Triton, Rust, pybind11, or Python bindings/tests.

## Do not use

- Architecture lock, directory isolation → `luminas-arch-skill`
- Ablations, p-values, venue structure → `research-skill`
- Upstream `spb2/` / `MoBA/` style matching

## Coding rules

### C99 CPU reference kernels

Applies to CPU reference and any portable scalar kernel, **not** to `.cu`.

1. C99 only. No C++, no GNU/MSVC extensions in these files.
2. Exported symbols `luma_*`; file-local `static`; macros `LUMA_*`.
3. Explicit allocation; NULL and bounds checks; no implicit grow.
4. Public APIs return `int` error codes. Do not report errors via `errno`.
5. IEEE 754 for the floating-point path you document in the header.

### CUDA C++ kernels

CUDA language extensions are allowed in `.cu` / `.cuh`.

1. Exported kernels / launchers `luma_cuda_*`. Grid and block are parameters, never literals for problem size.
2. Shared memory: no bank conflicts on the hot path; global loads vectorized / coalesced; prefer async copy where the arch supports it.
3. Check every runtime API and `cudaGetLastError()` after launch. Swallowing errors is a defect.
4. Numeric output matches the C99 reference under the L1/L5 gate in [references/test-matrix.md](references/test-matrix.md).
5. Tiling must run on GPU tiers **S=8 GB, M=24 GB, L=80 GB**. Do not claim a continuous 4–120 GB sweep.

### Triton

1. Exported ops `luma_triton_*`. Tile sizes are parameters; keep an autotune table.
2. No implicit cast or silent broadcast. Layout is explicit.
3. If a CUDA twin exists: same shape, same GPU, 2 warmup + 5 timed runs, Triton mean latency ≤ 1.11× CUDA mean (≈ 90% throughput). If no CUDA twin yet, report vs roofline only.

### Rust infra (optional layer)

1. Every `unsafe` block has a safety comment. No `unwrap`/`expect` on library paths.
2. `Result` + `Send`/`Sync` as required. No hidden global device state.

### Python scheduler

1. Glue, module wiring, train/infer entry, tests, **loop control** (Ouro-style). 
2. **No operator math and no KV encode/decode math** in Python. That belongs in `luma_*` / `luma_cuda_*` / `luma_triton_*`.
3. Public functions are fully annotated; `mypy` clean; no process-wide mutable cache.

### pybind11

1. Marshal, validate, translate errors. No numeric algorithm in the binding `.cpp`.
2. Check numpy dtype, rank, and c-contiguity; reject the rest with a clear error.
3. Release the GIL around kernel launches. Map `luma_*` codes to typed Python exceptions.

## Build

1. CMake: kernel / bind / tools as separate targets. One script or `cmake --build` target builds the tested pipeline.
2. Lock compiler, CUDA toolkit, driver family, and Python deps (`uv.lock`). Record versions in every benchmark report.
3. Conventional Commits; one concern per commit. Kernel behavior changes ship with an L1 test.

## Memory tiers

| Tier | VRAM | Default duty |
|---|---|---|
| S | 8 GB | Functional + degrade path |
| M | 24 GB | Default research GPU |
| L | 80 GB | 128k / large batch |

Implement a tile/pool path that **degrades** on OOM (smaller tiles, not silent abort). Degrade must still pass L5 if the kernel is on the lossless KV path. Use `compute-sanitizer` for device leaks; do not rely on `cuda-memcheck`.

## Tests (summary)

All `lumina/` modules: L1 unit, L2 boundary, L3 integration, L4 benchmark. Lossless KV paths also L5. Full gates and coverage: [references/test-matrix.md](references/test-matrix.md).

CI tools: pytest + xdist + Hypothesis; mypy + ruff; nsys / ncu / torch.profiler; compute-sanitizer; pytest-benchmark. Do not block a PR on MLPerf.

Engineering tests **do not** grant a "lossless" paper claim. That claim requires `research-skill`.

## Merge bar

- Static checks + L1–L3 green on the changed module.
- L4 if the change is on a hot kernel (throughput drop ≤ 2% vs last tagged baseline on the same tier).
- L5 if the change touches compress / decompress / residual.
- Release of a core algorithm additionally needs the research reports named in `research-skill`, bound to a commit hash.
