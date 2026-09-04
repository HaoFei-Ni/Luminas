/* luma_kv_codec.c — 产品路径 Enc/Dec（候选 KV-ENC-CANDIDATE-1）。
 *
 * 精确 float32 游程编码：码流为 (value, count) 浮点对；count 为可精确表示的
 * 正整数（≤2^24）。重构 bit-exact → 满足 2-ulp。可出现 enc_len < 2n；
 * 最坏（全互异）enc_len == 2n。禁止据此宣称论文级「无损」（须过三级门）。
 */
#include "luma_kv.h"
#include <math.h>
#include <string.h>

int luma_kv_require_finite_f32(const float *x, long n);

/* count 必须是可精确写入 float 的正整数，避免往返截断。 */
static int luma_kv_count_fits_f32(long count)
{
    return count >= 1 && count <= 16777216L;
}

/* 写出一对 (value,count)；容量不足返回 LUMA_ERR_ARG。 */
static int luma_kv_emit_run(float *enc, long enc_cap, long *out_i, float value, long count)
{
    long i = *out_i;

    if (!luma_kv_count_fits_f32(count))
        return LUMA_ERR_UNSUPPORTED;
    if (i > enc_cap - 2)
        return LUMA_ERR_ARG;
    enc[i] = value;
    enc[i + 1] = (float)count;
    *out_i = i + 2;
    return LUMA_OK;
}

/* 扫描一段等值游程，返回长度。 */
static long luma_kv_run_length(const float *x, long n, long start)
{
    float value = x[start];
    long end = start + 1;

    /* 必须 bit 级相同才并跑：避免近似相等破坏精确还原不变量。 */
    while (end < n && x[end] == value)
        ++end;
    return end - start;
}

/* 候选 Enc：有限性门后写 (value,count) 对；调用方 enc_cap 须 ≥2n（n>0）。 */
int luma_kv_encode_f32(const float *x, long n, float *enc, long enc_cap, long *enc_len)
{
    long i;
    long out_i;
    int rc;

    if (!x || !enc || !enc_len || n < 0 || enc_cap < 0)
        return LUMA_ERR_ARG;
    if (x == enc)
        return LUMA_ERR_ARG;
    if (n == 0) {
        *enc_len = 0;
        return LUMA_OK;
    }

    rc = luma_kv_require_finite_f32(x, n);
    if (rc != LUMA_OK)
        return rc;

    out_i = 0;
    i = 0;
    /* 变长游程必须扫描：无法在零循环下覆盖任意 n（门禁白名单）。 */
    while (i < n) {
        long run = luma_kv_run_length(x, n, i);

        rc = luma_kv_emit_run(enc, enc_cap, &out_i, x[i], run);
        if (rc != LUMA_OK)
            return rc;
        i += run;
    }
    *enc_len = out_i;
    return LUMA_OK;
}

/* 将一对 (value,count) 展开到 out；越界或 count 非法则失败。 */
static int luma_kv_expand_run(float *out, long n, long *filled, float value, float count_f)
{
    long count;
    long i;
    long base = *filled;

    if (!isfinite(count_f) || count_f < 1.0f)
        return LUMA_ERR_ARG;
    count = (long)count_f;
    if ((float)count != count_f || !luma_kv_count_fits_f32(count))
        return LUMA_ERR_ARG;
    if (base > n - count)
        return LUMA_ERR_ARG;
    /* 同值填充：count 已校验，避免逐元素分支抬高复杂度。 */
    for (i = 0; i < count; ++i)
        out[base + i] = value;
    *filled = base + count;
    return LUMA_OK;
}

/* 候选 Dec：成对消费码流并展开；filled 必须精确等于 n。 */
int luma_kv_decode_f32(const float *enc, long enc_len, float *out, long n)
{
    long i;
    long filled;
    int rc;

    if (!enc || !out || enc_len < 0 || n < 0)
        return LUMA_ERR_ARG;
    if (enc == out)
        return LUMA_ERR_ARG;
    if (n == 0) {
        if (enc_len != 0)
            return LUMA_ERR_ARG;
        return LUMA_OK;
    }
    if (enc_len == 0 || (enc_len & 1) != 0)
        return LUMA_ERR_ARG;

    rc = luma_kv_require_finite_f32(enc, enc_len);
    if (rc != LUMA_OK)
        return rc;

    filled = 0;
    i = 0;
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
