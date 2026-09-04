/* luma_kv_codec.c — 产品路径 Enc/Dec。
 *
 * 当前：有限性检查后的恒等映射，enc_len == n。
 * 占住 C-ABI / L1/L5 / theory 挂钩；不得冒充已发表压缩器。
 * 无显式 for：有限性见 finite.c；搬移用 memcpy。
 */
#include "luma_kv.h"
#include <string.h>

int luma_kv_require_finite_f32(const float *x, long n);

/* 恒等 Enc：enc_cap≥n；禁止原地；落地真压缩时只改本函数体。 */
int luma_kv_encode_f32(const float *x, long n, float *enc, long enc_cap, long *enc_len)
{
    int rc;

    if (!x || !enc || !enc_len || n < 0 || enc_cap < 0)
        return LUMA_ERR_ARG;
    if (x == enc)
        return LUMA_ERR_ARG;
    if (enc_cap < n)
        return LUMA_ERR_ARG;

    rc = luma_kv_require_finite_f32(x, n);
    if (rc != LUMA_OK)
        return rc;

    memcpy(enc, x, (size_t)n * sizeof(float));
    *enc_len = n;
    return LUMA_OK;
}

/* 恒等 Dec：要求 enc_len==n；真压缩器应在此按码流还原。 */
int luma_kv_decode_f32(const float *enc, long enc_len, float *out, long n)
{
    int rc;

    if (!enc || !out || enc_len < 0 || n < 0)
        return LUMA_ERR_ARG;
    if (enc == out)
        return LUMA_ERR_ARG;
    if (enc_len != n)
        return LUMA_ERR_ARG;

    rc = luma_kv_require_finite_f32(enc, enc_len);
    if (rc != LUMA_OK)
        return rc;

    memcpy(out, enc, (size_t)n * sizeof(float));
    return LUMA_OK;
}
