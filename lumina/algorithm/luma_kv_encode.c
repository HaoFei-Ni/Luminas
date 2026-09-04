/* luma_kv_encode.c — 产品 Enc（KV-ENC-CANDIDATE-1 精确 f32 RLE）。 */
#include "luma_kv.h"
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

/* 指针非空门。 */
static int luma_kv_encode_ptrs(const float *x, float *enc, long *enc_len)
{
    if (!x)
        return LUMA_ERR_ARG;
    if (!enc)
        return LUMA_ERR_ARG;
    if (!enc_len)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* 长度与别名门。 */
static int luma_kv_encode_bounds(const float *x, long n, float *enc, long enc_cap)
{
    if (n < 0)
        return LUMA_ERR_ARG;
    if (enc_cap < 0)
        return LUMA_ERR_ARG;
    if (x == enc)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

/* 参数门：指针/长度/别名；n==0 时写 *enc_len=0 并返回 OK。 */
static int luma_kv_encode_check(const float *x, long n, float *enc, long enc_cap, long *enc_len)
{
    int rc = luma_kv_encode_ptrs(x, enc, enc_len);

    if (rc != LUMA_OK)
        return rc;
    rc = luma_kv_encode_bounds(x, n, enc, enc_cap);
    if (rc != LUMA_OK)
        return rc;
    if (n != 0)
        return LUMA_OK;
    *enc_len = 0;
    return LUMA_OK;
}

/* 游程主体：调用方已保证有限输入与合法缓冲。 */
static int luma_kv_encode_runs(const float *x, long n, float *enc, long enc_cap, long *enc_len)
{
    long i = 0;
    long out_i = 0;
    int rc;

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

/* 产品 Enc：有限性门后写 (value,count) 对；调用方 enc_cap 须 ≥2n（n>0）。 */
int luma_kv_encode_f32(const float *x, long n, float *enc, long enc_cap, long *enc_len)
{
    int rc = luma_kv_encode_check(x, n, enc, enc_cap, enc_len);

    if (rc != LUMA_OK)
        return rc;
    if (n == 0)
        return LUMA_OK;
    rc = luma_kv_require_finite_f32(x, n);
    if (rc != LUMA_OK)
        return rc;
    return luma_kv_encode_runs(x, n, enc, enc_cap, enc_len);
}
