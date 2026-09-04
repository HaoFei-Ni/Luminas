/**
 * @file luma_quant_ternary.c
 * @brief 三值权重量化（有损基线，权重域）。
 *
 * 模型：w_i ≈ scale * codes_i，codes∈{-1,0,+1}。
 * scale = mean(|w|)；th = threshold * scale；|w|<th → 0。
 */
#include "baseline/luma_math.h"
#include "luma_kernel.h"

#include <math.h>

/** 已归一化阈值下的硬截断编码；无连续松弛，保证可复现对照。 */
static void luma_quant_ternary_body(const float *w, long n, float th, signed char *codes)
{
    long i;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < n; ++i) {
        float a = fabsf(w[i]);

        /* 硬阈值：|w|<th 置 0，否则符号位；无 STE/松弛。 */
        if (a >= th)
            codes[i] = (w[i] >= 0.0f) ? (signed char)1 : (signed char)-1;
        else
            codes[i] = 0;
    }
}

/* 导出入口：近零 scale 短路全零，避免除零与假阈值。 */
int luma_quant_ternary_encode(const float *w, float *scale, signed char *codes,
                              long n, float threshold)
{
    int rc;
    float s;

    if (!w || !scale || !codes || n < 0 || !isfinite(threshold) || threshold < 0.0f)
        return LUMA_ERR_ARG;
    if (n == 0) {
        *scale = 0.0f;
        return LUMA_OK;
    }

    rc = luma_math_require_finite_f32(w, n);
    if (rc != LUMA_OK)
        return rc;

    s = luma_math_mean_abs_f32(w, n);
    /* 近零均值：阈值无意义，整段零码并报 scale=0。 */
    if (s <= LUMA_TERNARY_NEAR_ZERO) {
        *scale = 0.0f;
        luma_math_fill_i8(codes, n, 0);
        return LUMA_OK;
    }

    *scale = s;
    /* th = threshold * mean(|w|)：相对阈值，与权重整体尺度无关。 */
    luma_quant_ternary_body(w, n, threshold * s, codes);
    return LUMA_OK;
}
