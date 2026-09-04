/* luma_kv_ref.c — 产品路径 FP64 预言机（theory P1/P2）。
 *
 * 语义必须保持「有限输入上的恒等复制」。encode/decode 换成真压缩算法后，
 * L5 仍用本函数当真值，禁止改成「跟当前有损核对齐」。
 */
#include "luma_kv.h"
#include <math.h>

int luma_kv_ref_copy_f64(const double *x, long n, double *out)
{
    long i;

    if (!x || !out || n < 0)
        return LUMA_ERR_ARG;

    /* n==0：合法空张量，不写内存。 */
    for (i = 0; i < n; ++i) {
        /* P5：非有限元直接失败，避免把 NaN 当无损通过。 */
        if (!isfinite(x[i]))
            return LUMA_ERR_NUMERIC;
        out[i] = x[i];
    }
    return LUMA_OK;
}
