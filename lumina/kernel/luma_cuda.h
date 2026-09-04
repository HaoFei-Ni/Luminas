/**
 * @file luma_cuda.h
 * @brief CUDA 有损基线启动器 ABI（设备指针由调用方持有）。
 *
 * @note 符号 luma_cuda_*：对照实验，不是产品无损 KV。
 *       threads_per_block 必须为 2 的幂且 ≤1024（归约实现依赖）。
 */
#ifndef LUMA_CUDA_H
#define LUMA_CUDA_H

#include "luma_kernel.h"

#include <cuda_fp16.h>
#include <cuda_runtime.h>

/** fused-decode 共享内存按此上限分配；超过返回 LUMA_ERR_UNSUPPORTED。 */
#define LUMA_CUDA_MAX_HEAD_DIM 256

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 每块 int8 量化：codes[i] ≈ round(clip(x[i]/scale_block, ±127))。
 *
 * @param[in] x 设备端输入，长度 n（fp16）
 * @param[out] codes 设备端码，长度 n
 * @param[out] scales 设备端块尺度，长度 ceil(n/block_size)
 * @param[in] n 元素数
 * @param[in] block_size 量化块长
 * @param[in] threads_per_block 2 的幂，≤1024
 * @param[in] stream CUDA 流，可为 0
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_CUDA
 *
 * @note 精度：对称 clip 到 ±127；有损，不套用 2-ulp 门。
 */
int luma_cuda_kv_quant_int8(const __half *x, signed char *codes, float *scales,
                            int n, int block_size, int threads_per_block,
                            cudaStream_t stream);

/**
 * @brief 融合 decode 参数包（入参 ≤5 门禁：单一结构体）。
 *
 * 布局（行主序）：
 *   x,out          [heads, d]
 *   Wq/Wk/Wv/Wo    [heads, d, d]
 *   Vt_r, V_code   [r, d]
 *   S_r            [r]
 *   k_tail,v_tail  [T, d]
 *   cos/sin_*      [d/2]   d 必须为偶数
 */
typedef struct luma_cuda_decode_fused_args {
    const __half *x;
    const __half *Wq;
    const __half *Wk;
    const __half *Wv;
    const __half *Wo;
    const __half *Vt_r;
    const float *S_r;
    const __half *V_code;
    const __half *k_tail;
    const __half *v_tail;
    const float *cos_q;
    const float *sin_q;
    const float *cos_k;
    const float *sin_k;
    int heads;
    int d;
    int r;
    int T;
    float scale;
    int threads_per_block;
    cudaStream_t stream;
    __half *out;
} luma_cuda_decode_fused_args_t;

/**
 * @brief 低秩背景 + 精确尾部的融合 decode（有损对照骨架）。
 *
 * @param[in] args 参数包；d ≤ LUMA_CUDA_MAX_HEAD_DIM
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_UNSUPPORTED | LUMA_ERR_CUDA
 *
 * @note 默认不编进库，见 LUMINA_BUILD_FUSED_DECODE。
 */
int luma_cuda_decode_fused(const luma_cuda_decode_fused_args_t *args);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_CUDA_H */
