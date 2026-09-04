/* luma_kv_decode.c — 产品 Dec（KV-ENC-CANDIDATE-1 精确 f32 RLE）。
 *
 * 工程 L5 / bit-exact：展开后长度必须等于 n；有限码流上与 Enc 互逆。
 * 非目标：有损近似解码。
 */
#include "luma_kv.h"
#include <math.h>

int luma_kv_require_finite_f32(const float *x, long n);

/* count 必须是可精确写入 float 的正整数，避免往返截断。 */
static int luma_kv_count_fits_f32(long count)
{
    return count >= 1 && count <= 16777216L;
}

/* 解析 count 浮点槽：非法则 ARG。 */
static int luma_kv_parse_count(float count_f, long *count_out)
{
    long count;

    if (!isfinite(count_f))
        return LUMA_ERR_ARG;
    if (count_f < 1.0f)
        return LUMA_ERR_ARG;
    count = (long)count_f;
    if ((float)count != count_f)
        return LUMA_ERR_ARG;
    if (!luma_kv_count_fits_f32(count))
        return LUMA_ERR_ARG;
    *count_out = count;
    return LUMA_OK;
}

/* 将一对 (value,count) 展开到 out；越界则失败。 */
static int luma_kv_expand_run(float *out, long n, long *filled, float value, float count_f)
{
    long count;
    long i;
    long base = *filled;
    int rc = luma_kv_parse_count(count_f, &count);

    if (rc != LUMA_OK)
        return rc;
    if (base > n - count)
        return LUMA_ERR_ARG;
    /* 同值填充：count 已校验，避免逐元素分支抬高复杂度。 */
    for (i = 0; i < count; ++i)
        out[base + i] = value;
    *filled = base + count;
    return LUMA_OK;
}

/* Decode 指针非空门。 */
static int luma_kv_decode_ptrs(const float *enc, float *out)
{
    if (!enc)
        return LUMA_ERR_ARG;
    if (!out)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* Decode 长度/别名门。 */
static int luma_kv_decode_bounds(const float *enc, long enc_len, float *out, long n)
{
    if (enc_len < 0)
        return LUMA_ERR_ARG;
    if (n < 0)
        return LUMA_ERR_ARG;
    if (enc == out)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* Decode 空张量与码长奇偶门。 */
static int luma_kv_decode_shape(long enc_len, long n)
{
    if (n == 0) {
        if (enc_len == 0)
            return LUMA_OK;
        return LUMA_ERR_ARG;
    }
    if (enc_len == 0)
        return LUMA_ERR_ARG;
    if ((enc_len & 1) != 0)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* Decode 参数门。 */
static int luma_kv_decode_check(const float *enc, long enc_len, float *out, long n)
{
    int rc = luma_kv_decode_ptrs(enc, out);

    if (rc != LUMA_OK)
        return rc;
    rc = luma_kv_decode_bounds(enc, enc_len, out, n);
    if (rc != LUMA_OK)
        return rc;
    return luma_kv_decode_shape(enc_len, n);
}

/* 成对展开码流；filled 必须在结束后等于 n。 */
static int luma_kv_decode_runs(const float *enc, long enc_len, float *out, long n)
{
    long i = 0;
    long filled = 0;
    int rc;

    /* 必须成对消费码流：奇数长度已拒绝，避免 count 槽位缺失。 */
    while (i < enc_len) {
        rc = luma_kv_expand_run(out, n, &filled, enc[i], enc[i + 1]);
        if (rc != LUMA_OK)
            return rc;
        i += 2;
    }
    if (filled != n)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* 产品 Dec：成对消费码流并展开；filled 必须精确等于 n。 */
int luma_kv_decode_f32(const float *enc, long enc_len, float *out, long n)
{
    int rc = luma_kv_decode_check(enc, enc_len, out, n);

    if (rc != LUMA_OK)
        return rc;
    if (n == 0)
        return LUMA_OK;
    rc = luma_kv_require_finite_f32(enc, enc_len);
    if (rc != LUMA_OK)
        return rc;
    return luma_kv_decode_runs(enc, enc_len, out, n);
}
