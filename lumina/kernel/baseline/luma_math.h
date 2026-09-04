/**
 * @file luma_math.h
 * @brief Level-1 数值原语：有限性、范数、尺度、别名检测（量化/SVD 共用）。
 *
 * @note 全部单层扫描；无递归。调用方负责缓冲寿命。
 */
#ifndef LUMA_MATH_H
#define LUMA_MATH_H

#include "baseline/luma_limits.h"

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 扫描 [0,n)：任一元非有限 → LUMA_ERR_NUMERIC。
 * @param[in] x 输入向量
 * @param[in] n 长度；n==0 视为 OK
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_math_require_finite_f32(const float *x, long n);

/**
 * @brief FP64 有限性门；SVD / 预言机路径专用。
 * @param[in] x 输入向量
 * @param[in] n 长度；n==0 视为 OK
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_math_require_finite_f64(const double *x, long n);

/**
 * @brief 半开区间 [start,end) 上 |x|_∞，并校验有限性。
 * @param[in] x 输入
 * @param[in] start 起点（含）
 * @param[in] end 终点（不含）
 * @param[out] amax_out 绝对值最大值
 * @return LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_math_absmax_f32(const float *x, long start, long end, float *amax_out);

/**
 * @brief mean(|x|)，double 累加防大 n 丢尾数。
 * @param[in] x 已保证有限的输入
 * @param[in] n 长度，须 >0
 * @return 平均绝对值
 */
float luma_math_mean_abs_f32(const float *x, long n);

/**
 * @brief 将 dst[0..n) 填为 v（n==0 无操作）。
 * @param[out] dst 目标
 * @param[in] n 长度
 * @param[in] v 填充值
 */
void luma_math_fill_i8(signed char *dst, long n, signed char v);

/**
 * @brief 块尺度：amax>0 → 2^{floor(log2(amax))}，否则 1。
 * @param[in] amax 块内绝对值最大
 * @return 正有限尺度；使 |x|/scale ∈ (0.5,2]（amax 为 2 的幂时取到 1）
 */
float luma_math_power_of_two_scale_f32(float amax);

/**
 * @brief 正数尾数量化：mbits+1 位定点（含隐含 1），away-from-zero。
 * @param[in] x 正有限输入
 * @param[in] mbits 尾数位宽
 * @return 量化后正数；非 OCP MX 的 RNE，仅有损对照
 */
float luma_math_quant_mantissa_pos_f32(float x, int mbits);

/**
 * @brief 指针字节区间是否重叠（禁止原地时用）。
 * @param[in] a 区间 A
 * @param[in] la A 字节长度
 * @param[in] b 区间 B
 * @param[in] lb B 字节长度
 * @return 非 0 表示重叠
 */
int luma_math_ptr_ranges_overlap(const void *a, size_t la, const void *b, size_t lb);

/**
 * @brief Level-1 点积（Gram / U 组装复用）。
 * @param[in] a 向量 A
 * @param[in] b 向量 B
 * @param[in] n 长度
 * @return Σ a[k]*b[k]
 */
double luma_math_dot_f64(const double *a, const double *b, int n);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_MATH_H */
