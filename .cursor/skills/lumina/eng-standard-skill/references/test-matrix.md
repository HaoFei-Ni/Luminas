# Luminas Engineering Test Matrix

CI-grade tests. Paper-grade PPL / task gates live in `research-skill`, not here.

## Five layers (every `lumina/` module)

| Layer | Question | Required artifacts | Gate |
|---|---|---|---|
| L1 Unit | Is the numeric function correct? | FP64 reference vs impl; max abs, RMSE, rel error | See numerical gate below |
| L2 Boundary | Does it survive ugly inputs? | Zero, empty, max shape, non-contiguous (must reject), NaN policy | No crash; documented return code or exception |
| L3 Integration | Do bind + scheduler + kernel agree? | One Python test that loads the extension and round-trips a known tensor | Bit-compare against the same C reference used in L1 |
| L4 Benchmark | Did we regress speed or memory? | 2 warmup + 5 timed runs; mean ± std | Throughput drop ≤ 2% vs last tagged baseline on the same GPU tier |
| L5 Lossless-numeric | Is a compression kernel numerically lossless? | Element error vs FP64; pass fraction | ≥ 99.9% elements within 2 ulp (definition in `research-skill` § lossless) |

L5 is mandatory only for KV-compress / decompress / residual paths. Other kernels stop at L1–L4.

## Stack, framework, coverage

Measure coverage on **`lumina/` only**, not upstream SpikingBrain trees.

| Stack | Framework | How to measure | Gate |
|---|---|---|---|
| C99 | Unity or CMocka + gcov/lcov | Line coverage on `luma_*` translation units | ≥ 95% lines; every exported `luma_*` has ≥ 1 L1 test |
| CUDA | Google Test (or Catch2) + `cudaGetLastError` after every launch | One L1 test per exported `luma_cuda_*` | 100% of exported kernels have an L1 test; do not claim "100% line coverage of `.cu`" |
| Triton | pytest | One L1 test per exported `luma_triton_*` | 100% of exported ops have an L1 test |
| Rust | `cargo test` + `cargo llvm-cov` | Line coverage; each `unsafe` block listed | ≥ 90% lines; 100% of `unsafe` blocks have a safety comment **and** a test that hits them |
| Python | pytest + pytest-xdist | `--cov=lumina` | Public API 100%; scheduler modules ≥ 90% |

Do not use "cuTest" or MLPerf as CI. MLPerf is an optional camera-ready systems suite, invoked only when the user asks.

## Numerical gate (L1 / L5)

Compare implementation output to an FP64 C reference on the same input.

- Reject non-finite outputs.
- Per-element pass: `|x - x64| ≤ 2 * 2^{-23} * max(1, |x64|)` (2 ulp in FP32 with an absolute floor).
- L1 (general kernels): 100% finite; document any kernel that is not intended to be 2-ulp faithful (e.g. BF16 accum) and give its own bound **in the test**.
- L5 (lossless KV path): ≥ 99.9% elements pass the 2-ulp test. This is the engineering half of the research lossless definition.

## Benchmark protocol (L4)

- Pin GPU tier: S = 8 GB, M = 24 GB, L = 80 GB. Record model, driver, CUDA, commit.
- Shapes: at least one shape per target sequence length 4k / 32k (128k on tier L only).
- Report: tokens/s or ms/iter, peak allocated bytes, estimated FLOP/s, bound type (compute vs bandwidth), TTFT if the path includes decode.
- 5 timed repeats after 2 warmup. Report mean ± std. No "best of N".

## Commands (defaults)

```text
cmake --build build --target lumina_test
ctest --test-dir build --output-on-failure
pytest -n auto lumina/tests
cargo test --manifest-path lumina/infra/Cargo.toml
```

Adapt paths if the tree differs; do not invent a second test root outside `lumina/`.
