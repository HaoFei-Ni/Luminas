/* luma_kv_ref.c — 产品路径 FP64 预言机（工程 L5 / 2-ulp）。
 *
 * 语义：有限输入上的恒等复制。encode/decode 换成真压缩后，L5 仍用本函数
 * 当真值，禁止改成「跟当前有损核对齐」。
 */
#include "luma_kv.h"
#include <string.h>

int luma_kv_require_finite_f64(const double *x, long n);

/* 指针与长度门。 */
static int luma_kv_ref_check(const double *x, long n, double *out)
{
    if (!x || !out)
        return LUMA_ERR_ARG;
    if (n < 0)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* n==0 合法空张量不写内存；有限性失败不得部分写出。 */
int luma_kv_ref_copy_f64(const double *x, long n, double *out)
{
    int rc = luma_kv_ref_check(x, n, out);

    if (rc != LUMA_OK)
        return rc;
    rc = luma_kv_require_finite_f64(x, n);
    if (rc != LUMA_OK)
        return rc;
    if (n > 0)
        memcpy(out, x, (size_t)n * sizeof(double));
    return LUMA_OK;
}
