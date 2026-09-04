# lumina/kernel

C99 / CUDA kernels for Luminas. Product symbols are `luma_kv_*`. Quantization, truncated SVD, and int8 KV are **baselines only**.

> **分层现状（2026-09，LUM-ARC-101 v1）**：物理分层（`algorithm/` / `kernel/` / `wrapper/`）已执行。本目录保留有损基线声明（`luma_kernel.h`）、CUDA launchers、有损基线实现。

## Layout

```text
lumina/kernel/
  luma_kernel.h                         public CPU lossy C-ABI (+ algorithm/luma_kv.h)
  luma_cuda.h                            CUDA launcher ABI
  luma_cuda.h                    compatibility shim → luma_cuda.h
  luma_cuda_util.h                       CUDA reduce / launch validate helpers
  baseline/
    luma_defs.h                          macros / tolerances (shared base)
    luma_math.h / luma_math.c            Level-1 primitives
    luma_svd.h                           private SVD contracts
    luma_svd_jacobi.c                    Jacobi eig + argsort
    luma_svd_gram.c                      Gram XtX / XXt
    luma_svd_truncated.c                 SVD driver (assemble U/S/Vt)
    luma_quant_ternary.c                 lossy weight ternary
    luma_quant_block_pow2.c              lossy power-of-two block quant
    luma_cuda_kv_quant_int8.cu           lossy int8 KV
    luma_cuda_decode_fused.cu            lossy low-rank+tail decode (opt-in)

  (C tests live in ../tests/c/ — see ../tests/README.md)

分层复用：量化与 SVD 共享 `luma_math`；SVD 子模块经 `luma_svd.h` 互链；
公共 ABI 只暴露 `luma_kernel.h` / `luma_cuda.h`。
```

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

## Naming

| Symbol prefix | Meaning |
|---|---|
| `luma_kv_*` / `luma_kv_ref_*` | Product lossless KV |
| `luma_math_*` | Shared Level-1 primitives |
| `luma_quant_*` / `luma_svd_*` | CPU lossy baselines |
| `luma_cuda_*` | CUDA launchers / device helpers |
| `LUMA_*` | Macros and error codes |

Do not name a truncated SVD or quantizer `lossless_*`.
