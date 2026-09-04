/* test_luma_kv.c — 产品路径 L1 / L2 / L5。
 *
 * L5：decode(encode(S_f32)) 与 FP64 预言机 luma_kv_ref_copy_f64 对照 2-ulp。
 * 通过本测试 ≠ 论文无损：lumina-res-skill 三级门仍待归档。
 */
#include "luma_kernel.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

static int g_fail;

static void expect_ok(int rc, const char *what)
{
    if (rc != LUMA_OK) {
        fprintf(stderr, "FAIL %s: %s (%d)\n", what, luma_strerror(rc), rc);
        g_fail = 1;
    }
}

/* |x-ref| <= 2 * 2^{-23} * max(1, |ref|) */
static int within_2ulp(float x, double ref)
{
    double lim = 2.0 * LUMA_ULP32 * (fabs(ref) > 1.0 ? fabs(ref) : 1.0);
    return fabs((double)x - ref) <= lim;
}

static void test_rle_roundtrip(void)
{
    float x[5] = {1.0f, -2.5f, 0.0f, 3.1415926f, 1e-3f};
    float enc[10], dec[5];
    double src64[5], ref64[5];
    long enc_len = 0;
    int i;

    expect_ok(luma_kv_encode_f32(x, 5, enc, 10, &enc_len), "encode");
    if (enc_len != 10) {
        fprintf(stderr, "FAIL distinct enc_len=%ld want 10\n", enc_len);
        g_fail = 1;
    }
    expect_ok(luma_kv_decode_f32(enc, enc_len, dec, 5), "decode");

    for (i = 0; i < 5; ++i)
        src64[i] = (double)x[i];
    expect_ok(luma_kv_ref_copy_f64(src64, 5, ref64), "ref");

    /* L5：重构必须贴着 FP64 预言机，而不是贴着输入 float。 */
    for (i = 0; i < 5; ++i) {
        if (!within_2ulp(dec[i], ref64[i])) {
            fprintf(stderr, "FAIL L5 dec[%d]=%g ref=%g\n", i, dec[i], ref64[i]);
            g_fail = 1;
        }
    }
}

static void test_rle_compresses_runs(void)
{
    float x[6] = {1.0f, 1.0f, 1.0f, 2.0f, 2.0f, 2.0f};
    float enc[12], dec[6];
    long enc_len = 0;

    expect_ok(luma_kv_encode_f32(x, 6, enc, 12, &enc_len), "encode runs");
    if (enc_len != 4) {
        fprintf(stderr, "FAIL run enc_len=%ld want 4\n", enc_len);
        g_fail = 1;
    }
    expect_ok(luma_kv_decode_f32(enc, enc_len, dec, 6), "decode runs");
    if (memcmp(x, dec, sizeof(x)) != 0) {
        fprintf(stderr, "FAIL run roundtrip mismatch\n");
        g_fail = 1;
    }
}

/* L2：空指针、负长度、空张量、NaN、容量不足、原地。 */
static void test_boundaries(void)
{
    float z = 0.0f, o = 0.0f;
    float nanv = NAN;
    long enc_len = 0;

    if (luma_kv_encode_f32(NULL, 1, &o, 2, &enc_len) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL null x\n");
    if (luma_kv_encode_f32(&z, -1, &o, 2, &enc_len) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL n<0\n");
    expect_ok(luma_kv_encode_f32(&z, 0, &o, 0, &enc_len), "n=0");
    if (luma_kv_encode_f32(&nanv, 1, &o, 2, &enc_len) != LUMA_ERR_NUMERIC)
        g_fail = 1, fprintf(stderr, "FAIL nan\n");
    if (luma_kv_encode_f32(&z, 1, &o, 0, &enc_len) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL enc_cap too small\n");
    if (luma_kv_encode_f32(&z, 1, &z, 2, &enc_len) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL in-place\n");
    if (luma_kv_decode_f32(&z, 0, &o, 1) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL decode len mismatch\n");
}

int main(void)
{
    test_rle_roundtrip();
    test_rle_compresses_runs();
    test_boundaries();
    if (g_fail) {
        fprintf(stderr, "test_luma_kv FAILED\n");
        return 1;
    }
    printf("test_luma_kv OK\n");
    return 0;
}
