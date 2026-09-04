/**
 * @file luma_kernel.h
 * @brief Luminas 内核稳定 C-ABI（绑定层唯一允许调用的 CPU 头）。
 *
 * 分层（LUM-ARC-101）：
 *   错误码 / 产品无损 KV 契约  → ../algorithm/luma_kv.h
 *   有损基线 luma_quant_* / luma_svd_* → kernel/baseline/
 *
 * 约定：返回 int 错误码；非有限输入 → LUMA_ERR_NUMERIC；调用方分配输出；禁止原地。
 */
#ifndef LUMA_KERNEL_H
#define LUMA_KERNEL_H

#include "baseline/luma_defs.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 三值权重量化 w ≈ scale * codes, codes∈{-1,0,+1}。
 *
 * @param[in] w 权重输入
 * @param[out] scale 输出尺度 mean(|w|)
 * @param[out] codes 三值码
 * @param[in] n 长度；n==0 时 *scale=0
 * @param[in] threshold 相对阈值系数，≥0 且有限
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 *
 * @note 权重域基线，不是 KV 压缩。精度：阈值硬截断，无连续松弛。
 */
int luma_quant_ternary_encode(const float *w, float *scale, signed char *codes,
                              long n, float threshold);

/**
 * @brief 块共享 power-of-two 尺度量化（非 OCP MX bit-exact）。
 *
 * @param[in] x 输入
 * @param[out] out 量化写回（不得与 x 重叠）
 * @param[in] n 长度
 * @param[in] mantissa_bits ∈ [0, LUMA_POW2_MAX_MANTISSA_BITS]
 * @param[in] block_size 块长，>0
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 *
 * @note 有损：不得套用 2-ulp 无损门。
 */
int luma_quant_block_pow2(const float *x, float *out, long n,
                          int mantissa_bits, int block_size);

/**
 * @brief 截断 SVD：X(m×n) ≈ U(m×r) diag(S) Vt(r×n)，行主序。
 *
 * @param[in] x 输入矩阵
 * @param[out] u 左奇异向量
 * @param[out] s 奇异值
 * @param[out] vt 右奇异向量（行）
 * @param[in] m 行数
 * @param[in] n 列数
 * @param[in] r 截断秩 ∈[1,min(m,n)]；dim=min(m,n)≤LUMA_JACOBI_MAX_DIM
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NOMEM | LUMA_ERR_NUMERIC | LUMA_ERR_UNSUPPORTED
 *
 * @note 高矩阵 G=XᵀX；宽矩阵 G=XXᵀ。r 截断必然有损。
 */
int luma_svd_truncated(const double *x, double *u, double *s, double *vt,
                       int m, int n, int r);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_KERNEL_H */
