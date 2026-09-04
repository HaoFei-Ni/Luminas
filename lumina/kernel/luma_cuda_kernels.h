/* luma_cuda_kernels.h — CUDA 启动器 ABI（仅基线核）。
 *
 * 符号前缀 luma_cuda_baseline_*：有损对照，不是产品无损 KV。
 * 设备指针由调用方分配；本头不包含数值算法。
 * threads_per_block 必须为 2 的幂且 ≤1024（归约实现依赖）。
 */
#ifndef LUMA_CUDA_KERNELS_H
#define LUMA_CUDA_KERNELS_H

#include "luma_kernels.h"
#include <cuda_fp16.h>
#include <cuda_runtime.h>

/* fused-decode 共享内存按此上限分配；超过返回 LUMA_ERR_UNSUPPORTED。 */
#define LUMA_CUDA_MAX_HEAD_DIM 256

#ifdef __cplusplus
extern "C" {
#endif

/* 每块 int8 量化：codes[i] ≈ round(clip(x[i]/scale_block, ±127))。
 * x, codes: 设备端，长度 n；scales: 设备端，长度 ceil(n/block_size)。
 * stream 可为 0。不在启动器里做 H2D。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_CUDA
 */
int luma_cuda_baseline_kv_int8(const __half *x, signed char *codes, float *scales,
                               int n, int block_size, int threads_per_block,
                               cudaStream_t stream);

/* 低秩背景 + 精确尾部的融合 decode（骨架）。
 *
 * 布局（行主序）：
 *   x,out          [heads, d]
 *   Wq/Wk/Wv/Wo    [heads, d, d]
 *   Vt_r, V_code   [r, d]
 *   S_r            [r]
 *   k_tail,v_tail  [T, d]
 *   cos/sin_*      [d/2]   d 必须为偶数
 *
 * d ≤ LUMA_CUDA_MAX_HEAD_DIM。默认不编进库，见 LUMINA_BUILD_FUSED_DECODE。
 */
int luma_cuda_baseline_fused_decode(
    const __half *x, const __half *Wq, const __half *Wk, const __half *Wv, const __half *Wo,
    const __half *Vt_r, const float *S_r, const __half *V_code,
    const __half *k_tail, const __half *v_tail,
    const float *cos_q, const float *sin_q, const float *cos_k, const float *sin_k,
    int heads, int d, int r, int T, float scale, int threads_per_block,
    cudaStream_t stream, __half *out);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_CUDA_KERNELS_H */
