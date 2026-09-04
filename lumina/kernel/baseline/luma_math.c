/**
 * @file luma_math.c
 * @brief Level-1 数值原语实现：量化与 SVD 共享，避免各核复制扫描。
 */
#include "baseline/luma_math.h"

#include <math.h>
#include <stddef.h>
#include <stdint.h>

/* 拒绝 NaN/Inf：否则下游尺度/奇异值会静默污染。 */
int luma_math_require_finite_f32(const float *x, long n)
{
    long i;

    if (!x || n < 0)
        return LUMA_ERR_ARG;
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < n; ++i)
        if (!isfinite(x[i]))
            return LUMA_ERR_NUMERIC;
    return LUMA_OK;
}

/* FP64 同语义；SVD 路径专用。 */
int luma_math_require_finite_f64(const double *x, long n)
{
    long i;

    if (!x || n < 0)
        return LUMA_ERR_ARG;
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < n; ++i)
        if (!isfinite(x[i]))
            return LUMA_ERR_NUMERIC;
    return LUMA_OK;
}

/* 块量化尺度的唯一输入；顺带有限性门禁。 */
int luma_math_absmax_f32(const float *x, long start, long end, float *amax_out)
{
    long i;
    float amax = 0.0f;

    if (!x || !amax_out || start < 0 || end < start)
        return LUMA_ERR_ARG;
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = start; i < end; ++i) {
        float a;

        if (!isfinite(x[i]))
            return LUMA_ERR_NUMERIC;
        a = fabsf(x[i]);
        if (a > amax)
            amax = a;
    }
    *amax_out = amax;
    return LUMA_OK;
}

/* double 累加：大 n 时 float 求和丢尾数，影响三值阈值。 */
float luma_math_mean_abs_f32(const float *x, long n)
{
    long i;
    double sum = 0.0;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < n; ++i)
        sum += (double)fabsf(x[i]);
    return (float)(sum / (double)n);
}

/* 近零权重整段置零码：避免阈值路径再扫一遍。 */
void luma_math_fill_i8(signed char *dst, long n, signed char v)
{
    long i;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < n; ++i)
        dst[i] = v;
}

/* 向下取 2 的幂尺度；amax<=0 回退 1 防 log 域错误。 */
float luma_math_pow2_floor_scale_f32(float amax)
{
    if (!(amax > 0.0f) || !isfinite(amax))
        return 1.0f;
    /* ldexp(1, floor(log2(amax))) ≡ 2^{⌊log₂ amax⌋}。 */
    return ldexpf(1.0f, (int)floorf(log2f(amax)));
}

/* 正数尾数 away-from-zero：对照基线，非 OCP MX RNE。 */
float luma_math_quant_mantissa_pos_f32(float x, int mbits)
{
    int e;
    float frac;
    float scale_bits;
    float q;

    frac = frexpf(x, &e); /* frac ∈ [0.5,1)，e 为二进制指数。 */
    /* mbits+1：含隐含前导 1 的定点格点；roundf 为 away-from-zero 对照策略。 */
    scale_bits = ldexpf(1.0f, mbits + 1);
    q = roundf(frac * scale_bits) / scale_bits;
    /* 按二进制指数重组装浮点。 */
    return ldexpf(q, e);
}

/* 半开字节区间重叠：禁止原地改写导致未定义别名。 */
int luma_math_ptr_ranges_overlap(const void *a, size_t la, const void *b, size_t lb)
{
    const uintptr_t pa = (uintptr_t)a;
    const uintptr_t pb = (uintptr_t)b;

    if (la == 0 || lb == 0 || !a || !b)
        return 0;
    /* 半开区间 [pa,pa+la) ∩ [pb,pb+lb) 非空。 */
    return (pa < pb + lb) && (pb < pa + la);
}

/* Level-1 点积：Gram / U 组装复用。 */
double luma_math_dot_f64(const double *a, const double *b, int n)
{
    int k;
    double acc = 0.0;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (k = 0; k < n; ++k)
        acc += a[k] * b[k];
    return acc;
}
