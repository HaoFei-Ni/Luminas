---
name: lumina-eng-skill
description: >-
  Enforces Luminas coding, build, and CI test standards for C99, CUDA, Triton,
  Rust, Python, and pybind11, including luma_ prefixes, numerical 2-ulp checks,
  physical algorithm/kernel/wrapper layering, and GPU memory tiers S=4 / M=24 /
  L=80 GB. Use when writing or reviewing kernels, bindings, CMake, tests, or
  benchmarks, or when the user mentions CUDA, Triton, kernel, 算子, nsys, ncu,
  coverage, pybind11, or luma_ prefixes. Do not use for paper structure, ablation
  design, architecture identity, or claiming lossless from unit tests alone.
paths:
  - "lumina/**"
  - "**/*.{c,h,cu,cuh}"
metadata:
  version: "3.1.0"
  owner: luminas
  domain: eng
  doc_prefix: LUM-ENG
---

# Luminas Engineering

Owns code, build, and **CI-grade** tests (product L1–L5 and theory F1–F7).
Does not redefine “lossless” and does not own paper experiments (`lumina-res-skill`).

## Priority

1. `lumina-arc-skill` — identity and non-goals
2. `lumina-eng-skill` — this file
3. `lumina-res-skill` — PPL / task / statistics / paper
4. Orchestra — baselines and tools only

Full gates and commands: [references/test-matrix.md](references/test-matrix.md).

## When to use

Writing or reviewing anything under `lumina/` in C, CUDA, Triton, Rust, pybind11, or Python bindings/tests.

## Do not use

- Architecture lock, directory isolation → `lumina-arc-skill`
- Ablations, p-values, venue structure → `lumina-res-skill`
- Matching upstream `spb2/` / `MoBA/` style as the implementation recipe

---

## Hard constraints (physical stack)

Highest-priority engineering rules for C/C++/CUDA under `lumina/`. Scope is mutually exclusive with the Transformer Python DDD rules in `.cursor/rules/transformer-python-standards.mdc`. Layering conflicts with the duty view → `LUM-ARC-101`.

### 1. Three orthogonal directories

No cross-layer calls, no reverse dependencies, no cyclic dependencies within a layer.

| Layer | Directory | Role | Must not |
|---|---|---|---|
| Algorithm | `algorithm/` | Platform-agnostic ANSI C; compress/decompress math only | System API, CUDA, side effects, global state |
| Kernel | `kernel/` | CUDA / CPU operators; hardware mapping and parallelism | Re-implement algorithm logic |
| Wrapper | `wrapper/` | Stable public API; platform diffs, memory, errors | Leak internal implementation in headers |

Headers expose the minimal contract only; implementations stay in `.c` / `.cu` / binding sources.

### 2. Zero runtime loop / recursion (hot path)

- No runtime `for` / `while` / `do-while` or recursion on the documented hot path.
- Replace linear scans with compile-time unroll, LUT, bit-batch ops, branch expand, SIMD, or full inline.
- Loops allowed only in compile-time macros / templates; recursion becomes LUT, iterative expand, or constexpr.

### 3. Structure metrics

| Scope | Limit |
|---|---|
| Header (`.h`) | ≤ 300 lines; declarations / macros / structs only |
| Implementation (`.c` / `.cu`) | ≤ 500 lines; split by duty if exceeded |
| Functions per file | ≤ 15 |
| Utility function | ≤ 50 lines |
| Core algorithm / operator function | ≤ 80 lines |
| Parameters | ≤ 5 (else pack a struct) |
| Cyclomatic complexity | ≤ 5 |
| `if` nesting | ≤ 2 |

One file = one module = one duty class.

### 4. Performance

- Memory 128-byte aligned; coalesced device access; no bank conflicts on the hot path.
- Prefer registers / shared memory; precompute offsets; no runtime address inventing.
- Prefer native hardware ops; compile-time constants; bit ops / LUT / predicates over branches.
- Small functions forced inline on the hot path; no indirect / virtual calls there.

### 5. Correctness

- Product lossless path: byte-level / 2-ulp contract as documented; cover empty, extreme length, misaligned, non-finite inputs.
- Bounds-check pointers; no wild pointers, OOB, leaks, double-free.
- Check CUDA alloc and `cudaGetLastError()` after launch.
- Named constants only; comment **why** on non-obvious hot-path transforms; clear error codes; no silent failure.

### 6. Execution principles

Single duty per module/function; minimize coupling; pass state explicitly; maximize compile-time work.

---

## Coding rules (by stack)

### C99 CPU reference

Applies to portable scalar / reference kernels — **not** `.cu`.

1. C99 only; no C++ or GNU/MSVC extensions in these files.
2. Exported symbols `luma_*`; file-local `static`; macros `LUMA_*`.
3. Explicit allocation; NULL and bounds checks; no implicit grow.
4. Public APIs return `int` error codes (not `errno`).
5. Document the IEEE 754 path in the header.

### CUDA C++

1. Exported kernels / launchers `luma_cuda_*`. Grid and block are parameters, never literals for problem size.
2. Shared memory: no bank conflicts on the hot path; vectorized / coalesced global loads; prefer async copy where supported.
3. Check every runtime API and `cudaGetLastError()` after launch.
4. Numeric output matches the C99 reference under L1/L5 in [references/test-matrix.md](references/test-matrix.md).
5. Tiling must run on GPU tiers **S = 4 GB, M = 24 GB, L = 80 GB**. Do not claim a continuous 4–120 GB sweep.

### Triton

1. Exported ops `luma_triton_*`. Tile sizes are parameters; keep an autotune table.
2. No implicit cast or silent broadcast; layout is explicit.
3. With a CUDA twin: same shape, same GPU, 2 warmup + 5 timed runs; Triton mean latency ≤ 1.11× CUDA mean. Without a twin: report vs roofline only.

### Rust infra (optional)

1. Every `unsafe` block has a safety comment; no `unwrap` / `expect` on library paths.
2. `Result` + `Send` / `Sync` as required; no hidden global device state.

### Python scheduler

1. Glue, wiring, train/infer entry, tests, loop **control** (Ouro-style) only.
2. No operator math and no KV encode/decode math in Python — use `luma_*` / `luma_cuda_*` / `luma_triton_*`.
3. Fully annotated public APIs; `mypy` clean; no process-wide mutable cache.

### pybind11

1. Marshal, validate, map errors; no numeric algorithm in the binding `.cpp`.
2. Check numpy dtype, rank, and C-contiguity; reject otherwise with a clear error.
3. Release the GIL around kernel launches; map `luma_*` codes to typed Python exceptions.

## Build

1. CMake: separate targets for kernel / bind / tools; one `cmake --build` path for the tested pipeline.
2. Lock compiler, CUDA toolkit, driver family, and Python deps (`uv.lock`); record versions in every benchmark report.
3. Conventional Commits; one concern per commit; kernel behavior changes ship with an L1 test.

## Memory tiers

| Tier | VRAM | Default duty |
|---|---|---|
| S | 4 GB | Functional + degrade path |
| M | 24 GB | Default research GPU |
| L | 80 GB | 128k / large batch |

On OOM, degrade (smaller tiles) — never silent abort. Degrade on the lossless KV path must still pass L5. Use `compute-sanitizer` for device leaks (not `cuda-memcheck`).

## Tests (summary)

| Track | IDs | Scope |
|---|---|---|
| Product | L1–L5 | `algorithm/` / `kernel/` / `wrapper/` / bindings; L5 only for compress / decompress / residual |
| Theory | F1–F7 | `theory/state-cache/verify/verify-degeneration.py`; orthogonal to L1–L5 |

Neither track grants a paper “lossless” claim — that requires `lumina-res-skill`.

CI tools: pytest + xdist + Hypothesis; mypy + ruff; nsys / ncu / torch.profiler; compute-sanitizer; pytest-benchmark. Do not block a PR on MLPerf.

## Merge bar

- Static checks + L1–L3 green on the changed module.
- L4 if the change is on a hot kernel (throughput drop ≤ 2% vs last tagged baseline on the same tier).
- L5 if the change touches compress / decompress / residual.
- F1–F7 E-layer if the change touches `theory/state-cache/framework.*` or `verify-degeneration.py` (MC when closed-form constants or proof-facing bounds change).
- Core-algorithm release also needs `lumina-res-skill` reports bound to a commit hash.

## Related documents

| Doc | Role |
|---|---|
| `lumina/docs/eng/LUM-ENG-001` | Engineering overview |
| `lumina/docs/eng/LUM-ENG-101` | Language / naming standards |
| `lumina/docs/eng/LUM-ENG-201` | Build and dependencies |
| `lumina/docs/eng/LUM-ENG-301` | Test toolchain entry |

## Additional resources

- [references/test-matrix.md](references/test-matrix.md)
