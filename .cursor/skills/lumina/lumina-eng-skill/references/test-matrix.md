# Luminas Engineering Test Matrix

CI-grade tests. Paper-grade PPL / task gates live in `lumina-res-skill`, not here.

## Tracks (do not conflate)

| Track | Scope | IDs | Grants “lossless KV”? |
|---|---|---|---|
| Product kernels | `algorithm/` / `kernel/` / `wrapper/` / bindings | **L1–L5** | No — L5 is the engineering half only; paper claim needs `lumina-res-skill` |
| Theory verifier | `theory/state-cache/` (表征坍缩统一理论) | **F1–F7** | No — spectral rank / SVT closed forms only |

Authoritative theory draft: `lumina/theory/state-cache/framework.tex` (readable: `framework.md`).

GPU memory tiers: **S = 4 GB / M = 24 GB / L = 80 GB**.

---

## Product layers (L1–L5)

| Layer | Question | Required artifacts | Gate |
|---|---|---|---|
| L1 Unit | Is the numeric function correct? | FP64 reference vs impl; max abs, RMSE, rel error | See numerical gate below |
| L2 Boundary | Does it survive ugly inputs? | Zero, empty, max shape, non-contiguous (must reject), NaN policy | No crash; documented return code or exception |
| L3 Integration | Do bind + scheduler + kernel agree? | One Python test that loads the extension and round-trips a known tensor | Bit-compare against the same C reference used in L1 |
| L4 Benchmark | Did we regress speed or memory? | 2 warmup + 5 timed runs; mean ± std | Throughput drop ≤ 2% vs last tagged baseline on the same GPU tier |
| L5 Lossless-numeric | Is a compression kernel numerically lossless? | Element error vs FP64; pass fraction | ≥ 99.9% elements within 2 ulp (`lumina-res-skill` Level 1) |

L5 is mandatory only for KV compress / decompress / residual paths. Other kernels stop at L1–L4.

---

## Theory track (F1–F7)

Not a substitute for L1–L5. Pure Python standard library; fixed seed `SEED = 20240904`.

| ID | Claim | Gate | Entry |
|---|---|---|---|
| F1 | Spectral-gap rank recovery | δ < γ/2 → exact r̂ = r; δ ≥ γ → rank drop exists | E + MC (5000/5000) |
| F2 | Eckart–Young residual | \|‖A−A_k‖_F² − Σ_{i>k} σ_i²\| < 10⁻⁹ | E + MC |
| F3 | Weyl / Mirsky | Excess ≤ 0; ℓ₂ violations = 0 | E + MC |
| F4 | Sylvester rank bound | #{rank(XW) > min} = 0 | E + MC |
| F5 | ReLU rank increase (boundary) | Exact 1 → 2 counterexample | E |
| F6 | SVT closed form | Rank violations = 0; spectral deviation < 10⁻⁹ | E + MC |
| F7 | Critical collapse time | Closed form vs Euler < 10⁻⁶ | E |

Verifier layers (orthogonal to product L1–L5):

| Layer | Flag | Role |
|---|---|---|
| E | default | Small exact examples; must exit 0 |
| MC | `--mc` | Large-sample falsification; zero violations |
| DATA | `--data` | Contract `degeneration-v1` |

**Legacy:** `check_identity.py` is not an F-series gate. Product KV comments use **L5 / 2-ulp**, not F1–F7.

---

## Stack coverage

Measure coverage on **`lumina/` only**, not upstream SpikingBrain trees.

| Stack | Framework | How to measure | Gate |
|---|---|---|---|
| C99 | Unity or CMocka + gcov/lcov | Line coverage on `luma_*` TUs | ≥ 95% lines; every exported `luma_*` has ≥ 1 L1 test |
| CUDA | Google Test (or Catch2) + `cudaGetLastError` after every launch | One L1 test per exported `luma_cuda_*` | 100% of exported kernels have an L1 test |
| Triton | pytest | One L1 test per exported `luma_triton_*` | 100% of exported ops have an L1 test |
| Rust | `cargo test` + `cargo llvm-cov` | Line coverage; each `unsafe` listed | ≥ 90% lines; 100% of `unsafe` blocks have safety comment **and** a hitting test |
| Python (product) | pytest + xdist | `--cov=lumina` (exclude `theory/*`) | Public API 100%; scheduler ≥ 90% |
| Python (theory) | `verify-degeneration.py` | F1–F7 E-layer exit 0 | Not counted in product `--cov` |

Do not use “cuTest” or MLPerf as CI. MLPerf is optional camera-ready, invoked only on request.

---

## Numerical gate (L1 / L5)

Compare implementation output to an FP64 C reference on the same input.

- Reject non-finite outputs.
- Per-element pass: `|x − x64| ≤ 2 · 2⁻²³ · max(1, |x64|)`.
- L1 (general): 100% finite; document any non-2-ulp-intended kernel with its own bound **in the test**.
- L5 (lossless KV path): ≥ 99.9% elements pass 2-ulp.

Theory F2 / F6 / F7 use the absolute tolerances in the F table — do not mix into product L5.

---

## Benchmark protocol (L4)

- Pin GPU tier: **S = 4 GB**, M = 24 GB, L = 80 GB. Record model, driver, CUDA, commit.
- Shapes: at least one shape per target length 4k / 32k (128k on tier L only).
- Report: tokens/s or ms/iter, peak allocated bytes, estimated FLOP/s, bound type, TTFT if decode is included.
- 5 timed repeats after 2 warmup. Report mean ± std. No best-of-N.

---

## Commands

```text
# Product CI
cmake --build build --target lumina_test
ctest --test-dir build --output-on-failure
pytest -n auto lumina/tests
cargo test --manifest-path lumina/infra/Cargo.toml

# Theory F1–F7 (cwd: lumina/theory/state-cache/verify/)
python verify-degeneration.py
python verify-degeneration.py --mc
python verify-degeneration.py --print-template
```

Do not invent a second product test root outside `lumina/tests` / ctest. Theory scripts stay under `lumina/theory/state-cache/verify/`.

---

## Merge bar

| Change touches… | Required green |
|---|---|
| Product kernel / bind / codec | Static + L1–L3; L4 if hot path; L5 if compress/decompress/residual |
| `theory/state-cache/framework.*` or `verify-degeneration.py` | F1–F7 E-layer (exit 0); MC if closed-form constants / proof-facing bounds change |
| Both | Both tracks |

Engineering / theory greens **do not** grant a paper “lossless” claim. That claim requires `lumina-res-skill`.
