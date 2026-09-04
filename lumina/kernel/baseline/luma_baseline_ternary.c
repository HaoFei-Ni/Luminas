/* luma_baseline_ternary.c — 三值权重量化（有损基线，权重域）。
 *
 * 模型：w_i ≈ scale * codes_i，codes_i ∈ {-1,0,+1}。
 * scale = mean(|w|)，阈值 th = threshold * scale，|w|<th 置零。
 *
 * 这是 TWN 类对照，不是状态缓存压缩，禁止当作 luma_kv_* 产品路径。
 */
#include "luma_kernels.h"
#include <math.h>

int luma_baseline_ternary_encode(const float *w, long n, float threshold,
                                 float *scale, signed char *codes)
{
    long i;
    double sum;
    float s, th;

    if (!w || !scale || !codes || n < 0 || !isfinite(threshold) || threshold < 0.0f)
        return LUMA_ERR_ARG;
    if (n == 0) {
        *scale = 0.0f;
        return LUMA_OK;
    }

    /* 用 double 累加 |w|，避免大 n 时 float 求和漂移。 */
    sum = 0.0;
    for (i = 0; i < n; ++i) {
        if (!isfinite(w[i]))
            return LUMA_ERR_NUMERIC;
        sum += (double)fabsf(w[i]);
    }
    s = (float)(sum / (double)n);

    /* 近零权重：全部编码为 0，避免除零和假阈值。 */
    if (s <= 1e-12f) {
        *scale = 0.0f;
        for (i = 0; i < n; ++i)
            codes[i] = 0;
        return LUMA_OK;
    }

    *scale = s;
    th = threshold * s;
    for (i = 0; i < n; ++i) {
        float a = fabsf(w[i]);
        if (a >= th)
            codes[i] = (w[i] >= 0.0f) ? (signed char)1 : (signed char)-1;
        else
            codes[i] = 0;
    }
    return LUMA_OK;
}
