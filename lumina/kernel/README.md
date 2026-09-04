# lumina/kernel

C99 / CUDA kernels for Luminas. Product symbols are `luma_kv_*`. Quantization, truncated SVD, and int8 KV are **baselines only**.

> **分层现状（2026-09，LUM-ARC-101 v1）**：物理分层（`algorithm/` / `kernel/` / `wrapper/`）已执行 Phase A + Phase B 迁移——产品路径源与契约头（`luma_kv.h`、`luma_status.c`）移至 `../algorithm/`，pybind 绑定移至 `../wrapper/`（见 `../docs/arc/LUM-ARC-101`）。本目录保留有损基线声明（`luma_kernels.h`）、CUDA launchers、有损基线与测试。

## Layout

```text
lumina/kernel/
  luma_kernels.h                         baseline C-ABI (includes ../algorithm/luma_kv.h)
  luma_cuda_kernels.h                    CUDA launchers (incl. LUMA_CUDA_MAX_HEAD_DIM)
  luma_cuda_util.h                       shared host/device utils (is_pow2 / reduce_sum)
  baseline/
    luma_baseline_ternary.c              lossy weight ternary
    luma_baseline_pow2_block_quant.c      lossy power-of-two block quant
    luma_baseline_truncated_svd.c        lossy Gram+Jacobi SVD
    luma_cuda_baseline_kv_int8.cu        lossy int8 KV
    luma_cuda_baseline_fused_decode.cu   lossy low-rank+tail decode (opt-in)
    20|
  (C tests live in ../tests/c/ — see ../tests/README.md)

分层迁移（LUM-ARC-101 Phase A + B）：
  ../algorithm/luma_kv.h                 algorithm contract (errors + product decls)
  ../algorithm/luma_status.c             error strings
  ../algorithm/luma_kv_ref.c             FP64 oracle
  ../algorithm/luma_kv_codec.c             product Enc/Dec
  ../wrapper/luma_bind_native.cpp        pybind11 marshal for CPU
  ../wrapper/luma_bind_cuda.cpp          pybind11 marshal for CUDA baselines
```

`luma_kv_encode_f32` / `luma_kv_decode_f32` are a finite-checked **identity** with `enc_len == n`. That is the ABI and the 2-ulp oracle, not a published compressor. Do not report a compression ratio for them. `decode` takes the encoded buffer and its length plus the target length `n`; the identity path requires `enc_len == n`.

Method math (P0–P5) lives in [`lumina/theory/state-cache/`](../theory/state-cache/README.md). Implement formulas here; do not store the derivation in this directory.

## Build

```bash
cmake -S lumina -B outputs/build/lumina
cmake --build outputs/build/lumina
ctest --test-dir outputs/build/lumina --output-on-failure
```

Optional:

```bash
cmake -S lumina -B outputs/build/lumina \
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
