/* luma_baseline_pow2_block_quant.c — 块共享 2 次幂尺度的尾数量化（有损基线）。
 *
 * 不是 OCP MX 规范的 bit-exact 实现，只复现「每块一个 power-of-two scale」
 * 这一对照思路。重构误差远大于 2-ulp，不得称无损。
 */
#include "luma_kernels.h"
#include <math.h>

/* 对正数做 mbits+1 位定点取整（含隐含前导位），再按 frexp 指数还原。
 * 取整用 roundf（away-from-zero），不是 OCP 的 round-to-nearest-even。
 * mbits 已由调用方限制在 [0, 23]，ldexpf(1, mbits+1) 不会移位溢出。 */
static float luma_quant_positive(float x, int mbits)
{
    int e;
    float frac, scale_bits, q;

    frac = frexpf(x, &e); /* frac ∈ [0.5, 1) */
    scale_bits = ldexpf(1.0f, mbits + 1);
    q = roundf(frac * scale_bits) / scale_bits;
    return ldexpf(q, e);
}

int luma_baseline_pow2_block_quant(const float *x, long n, int mantissa_bits,
                             int block_size, float *out)
{
    long start;

    if (!x || !out || n < 0 || block_size <= 0)
        return LUMA_ERR_ARG;
    if (mantissa_bits < 0 || mantissa_bits > LUMA_POW2_BLOCK_MAX_MANTISSA_BITS)
        return LUMA_ERR_ARG;

    for (start = 0; start < n; start += block_size) {
        long end = start + block_size;
        long i;
        float amax = 0.0f;
        float scale;

        if (end > n)
            end = n; /* 末块允许短于 block_size */

        for (i = start; i < end; ++i) {
            float a;

            if (!isfinite(x[i]))
                return LUMA_ERR_NUMERIC;
            a = fabsf(x[i]);
            if (a > amax)
                amax = a;
        }

        /* 块内最大幅值向下取到 2 的幂，使 |x|/scale 落在约 (0.5, 2]。 */
        scale = (amax > 0.0f) ? ldexpf(1.0f, (int)floorf(log2f(amax))) : 1.0f;
        for (i = start; i < end; ++i) {
            float v = fabsf(x[i]) / scale;
            float q = (v > 0.0f) ? luma_quant_positive(v, mantissa_bits) : 0.0f;
            out[i] = copysignf(q * scale, x[i]);
        }
    }
    return LUMA_OK;
}
