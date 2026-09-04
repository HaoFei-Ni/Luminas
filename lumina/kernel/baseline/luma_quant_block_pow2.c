/**
 * @file luma_quant_block_pow2.c
 * @brief 块共享 power-of-two 尺度尾数量化（有损基线）。
 *
 * 非 OCP MX bit-exact：away-from-zero round + 每块 2^{floor(log2(amax))}。
 */
#include "baseline/luma_math.h"
#include "luma_kernels.h"

#include <math.h>

/** 固定块尺度下写回；scale 已由 pow2_floor 保证 >0。 */
static void luma_quant_block_encode(const float *x, long start, long end,
                                    float scale, int mantissa_bits, float *out)
{
    long i;

    for (i = start; i < end; ++i) {
        /* 先归一到 (0.5,2] 量级再量化尾数，再乘回尺度并恢复符号。 */
        float v = fabsf(x[i]) / scale;
        float q = (v > 0.0f) ? luma_math_quant_mantissa_pos_f32(v, mantissa_bits) : 0.0f;

        out[i] = copysignf(q * scale, x[i]);
    }
}

/** 单块：amax→尺度→编码；拆出外层循环以满足单层循环门禁。 */
static int luma_quant_block_one(const float *x, long start, long end,
                                int mantissa_bits, float *out)
{
    float amax = 0.0f;
    float scale;
    int rc;

    rc = luma_math_absmax_f32(x, start, end, &amax);
    if (rc != LUMA_OK)
        return rc;
    /* floor(log2(amax)) 使块内 |x|/scale ∈ (0.5,2]，利于定点尾数。 */
    scale = luma_math_pow2_floor_scale_f32(amax);
    luma_quant_block_encode(x, start, end, scale, mantissa_bits, out);
    return LUMA_OK;
}

/* 导出入口：拒绝原地缓冲；末块允许短于 block_size。 */
int luma_quant_block_pow2(const float *x, float *out, long n,
                          int mantissa_bits, int block_size)
{
    long start;

    if (!x || !out || n < 0 || block_size <= 0)
        return LUMA_ERR_ARG;
    /* mbits≥24 会使 1<<(mbits+1) 超出 float 尾数安全移位。 */
    if (mantissa_bits < 0 || mantissa_bits > LUMA_POW2_MAX_MANTISSA_BITS)
        return LUMA_ERR_ARG;
    /* 原地量化会边读边写，破坏块内 amax 语义。 */
    if (luma_math_ptr_ranges_overlap(x, (size_t)n * sizeof(float), out,
                                     (size_t)n * sizeof(float)))
        return LUMA_ERR_ARG;

    for (start = 0; start < n; start += block_size) {
        long end = start + block_size;
        int rc;

        if (end > n)
            end = n; /* 末块变短，尺度仍按该短块 amax。 */
        rc = luma_quant_block_one(x, start, end, mantissa_bits, out);
        if (rc != LUMA_OK)
            return rc;
    }
    return LUMA_OK;
}
