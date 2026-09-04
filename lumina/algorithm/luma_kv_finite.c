/* luma_kv_finite.c — 有限性扫描（algorithm 唯一允许的必要单层循环）。
 *
 * lumina-eng-skill：algorithm 运行时零循环；变长 NaN/Inf 门禁在落地 SIMD/LUT
 * 真 Enc 前只能显式扫描。函数名列入 quality-gate loop_allowed_functions。
 */
#include "luma_kv.h"
#include <math.h>

/* FP32：非有限元会使恒等 Enc 与 2-ulp 对照失真。 */
int luma_kv_require_finite_f32(const float *x, long n)
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

/* FP64 预言机路径同语义。 */
int luma_kv_require_finite_f64(const double *x, long n)
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
