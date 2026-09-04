/* luma_kv_codec.c — 产品路径 Enc/Dec。
 *
 * 当前实现：有限性检查后的恒等映射，enc_len == n。
 * 目的：占住 C-ABI、L1/L5 与 theory/state-cache 的挂钩，而不是冒充已发表压缩器。
 *
 * 落地公式时：
 *   1. 只改本文件函数体；
 *   2. 保持错误码语义；
 *   3. 继续用 luma_kv_ref_copy_f64 做 2-ulp 对照；
 *   4. 未过 research-skill 三级门之前不得称无损，不得报 ρ。
 */
#include "luma_kv.h"
#include <math.h>

int luma_kv_encode_f32(const float *x, long n, float *enc, long enc_cap, long *enc_len)
{
    long i;

    if (!x || !enc || !enc_len || n < 0 || enc_cap < 0)
        return LUMA_ERR_ARG;
    if (x == enc)
        return LUMA_ERR_ARG; /* 禁止原地 */
    if (enc_cap < n)
        return LUMA_ERR_ARG; /* 恒等实现需要 n 个槽位 */

    for (i = 0; i < n; ++i) {
        if (!isfinite(x[i]))
            return LUMA_ERR_NUMERIC;
        /* 占位：Enc = Id。真 Enc 应写更短或等长的压缩表示。 */
        enc[i] = x[i];
    }
    *enc_len = n;
    return LUMA_OK;
}

int luma_kv_decode_f32(const float *enc, long enc_len, float *out, long n)
{
    long i;

    if (!enc || !out || enc_len < 0 || n < 0)
        return LUMA_ERR_ARG;
    if (enc == out)
        return LUMA_ERR_ARG;
    if (enc_len != n)
        return LUMA_ERR_ARG; /* 恒等实现：压缩域长度必须等于原长 */

    for (i = 0; i < n; ++i) {
        if (!isfinite(enc[i]))
            return LUMA_ERR_NUMERIC;
        out[i] = enc[i];
    }
    return LUMA_OK;
}
