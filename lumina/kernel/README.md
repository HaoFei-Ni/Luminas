# lumina/kernel

C99 / CUDA kernels for Luminas. Product symbols are `luma_kv_*`. Quantization, truncated SVD, and int8 KV are **baselines only**.

> **分层现状（2026-09）**：物理目录规划（`algorithm/` / `kernel/` / `wrapper/`）见 `../docs/arc/LUM-ARC-101`；本目录为现有代码所在地，迁移按该裁决执行，须同步本 README 与 `CMakeLists.txt`。尚未迁移前，现有文件保持当前位置。

## Layout

```text
lumina/kernel/
  luma_kernels.h                         C-ABI (only header bindings may call)
  luma_status.c / luma_kv_ref.c / luma_kv_cpu.c
  luma_bind_native.cpp                   pybind11 marshal for CPU
  luma_bind_cuda.cpp                     pybind11 marshal for CUDA baselines
  luma_cuda_kernels.h                    CUDA launchers
  baseline/
    luma_baseline_ternary.c              lossy weight ternary
    luma_baseline_mxfp.c                 lossy MXFP-style block quant
    luma_baseline_truncated_svd.c        lossy Gram+Jacobi SVD
    luma_cuda_baseline_kv_int8.cu        lossy int8 KV
    luma_cuda_baseline_fused_decode.cu   lossy low-rank+tail decode (opt-in)
  test/
    test_luma_kv.c                       L1/L2/L5 product path
    test_luma_baseline.c                 L1/L2 baselines
```

`luma_kv_encode_f32` / `luma_kv_decode_f32` are a finite-checked **identity** with `enc_len == n`. That is the ABI and the 2-ulp oracle, not a published compressor. Do not report a compression ratio for them. `decode` takes the encoded buffer and its length plus the target length `n`; the identity path requires `enc_len == n`.

Method math (P0–P5) lives in [`lumina/theory/state-cache/`](../theory/state-cache/README.md). Implement formulas here; do not store the derivation in this directory.

## Build

```bash
cmake -S lumina/kernel -B outputs/build/kernel
cmake --build outputs/build/kernel
ctest --test-dir outputs/build/kernel --output-on-failure
```

Optional:

```bash
cmake -S lumina/kernel -B outputs/build/kernel \
  -DLUMINA_BUILD_CUDA=ON \
  -DLUMINA_BUILD_FUSED_DECODE=ON
```

Python modules (`_luma_native`, `_luma_cuda`) build only when pybind11 is found. Scheduler code must go through an isolation layer; do not import `_luma_*` from model code.

## Naming

| Symbol prefix | Meaning |
|---|---|
| `luma_kv_*` / `luma_kv_ref_*` | Product lossless KV |
| `luma_baseline_*` | CPU lossy controls |
| `luma_cuda_baseline_*` | GPU lossy controls |
| `luma_cuda_*` | CUDA launchers (engineering prefix) |
| `LUMA_*` | Macros and error codes |

Do not name a truncated SVD or quantizer `lossless_*`.
