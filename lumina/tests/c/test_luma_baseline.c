/* test_luma_baseline.c — 有损基线的 L1/L2。
 *
 * 不套用 2-ulp 无损门。SVD 只在满秩时检查重构残差（验证 Jacobi，不是无损宣称）。
 */
#include "luma_kernels.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

static int g_fail;

/* 测试容差（具名，禁止散落裸数字）。 */
#define LUMA_TEST_FRO_DENOM_EPS 1e-30 /* fro_recon 分母保护 */
#define LUMA_TEST_SVD_RECON_TOL 1e-8  /* 满秩 SVD 重构残差阈值 */

static void expect_ok(int rc, const char *what)
{
    if (rc != LUMA_OK) {
        fprintf(stderr, "FAIL %s: %s (%d)\n", what, luma_strerror(rc), rc);
        g_fail = 1;
    }
}

/* ||X - U S Vt||_F / ||X||_F */
static double fro_recon(const double *x, const double *u, const double *s, const double *vt,
                        int m, int n, int r)
{
    int i, j, k;
    double err = 0.0, nrm = 0.0;

    for (i = 0; i < m; ++i) {
        for (k = 0; k < n; ++k) {
            double acc = 0.0;
            for (j = 0; j < r; ++j)
                acc += u[i * r + j] * s[j] * vt[j * n + k];
            err += (acc - x[i * n + k]) * (acc - x[i * n + k]);
            nrm += x[i * n + k] * x[i * n + k];
        }
    }
    return sqrt(err) / (sqrt(nrm) + LUMA_TEST_FRO_DENOM_EPS);
}

static void test_ternary(void)
{
    float w[4] = {1.0f, -0.01f, 0.8f, 0.0f};
    signed char codes[4];
    float scale = 0.0f;

    expect_ok(luma_baseline_ternary_encode(w, 4, 0.5f, &scale, codes), "ternary");
    /* |w1| 远小于 0.5*mean(|w|)，应被置零。 */
    if (codes[0] != 1 || codes[2] != 1 || codes[3] != 0) {
        fprintf(stderr, "FAIL ternary codes\n");
        g_fail = 1;
    }
    if (luma_baseline_ternary_encode(w, 4, -1.0f, &scale, codes) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL ternary threshold\n");
}

static void test_pow2_block(void)
{
    float x[5] = {1.0f, -1.0f, 0.25f, 0.0f, 2.0f};
    float out[5];

    expect_ok(luma_baseline_pow2_block_quant(x, 5, 3, 2, out), "pow2_block");
    if (out[3] != 0.0f) {
        fprintf(stderr, "FAIL pow2_block zero\n");
        g_fail = 1;
    }
    /* mbits=40 超过 LUMA_POW2_BLOCK_MAX_MANTISSA_BITS。 */
    if (luma_baseline_pow2_block_quant(x, 5, 40, 2, out) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL pow2_block mbits\n");
}

static void test_svd_full_rank(void)
{
    /* 高 4×3：走 XᵀX */
    double xt[12] = {
        1, 0, 0,
        0, 2, 0,
        0, 0, 3,
        1, 1, 1
    };
    double u[12], s[3], vt[9];
    /* 宽 2×4：走 XXᵀ */
    double xw[8] = {
        1, 2, 3, 4,
        0, 1, 0, 1
    };
    double uw[4], sw[2], vtw[8];
    double rel;

    expect_ok(luma_baseline_truncated_svd(xt, 4, 3, 3, u, s, vt), "svd tall");
    rel = fro_recon(xt, u, s, vt, 4, 3, 3);
    if (rel > LUMA_TEST_SVD_RECON_TOL) {
        fprintf(stderr, "FAIL svd tall residual %g\n", rel);
        g_fail = 1;
    }

    expect_ok(luma_baseline_truncated_svd(xw, 2, 4, 2, uw, sw, vtw), "svd wide");
    rel = fro_recon(xw, uw, sw, vtw, 2, 4, 2);
    if (rel > LUMA_TEST_SVD_RECON_TOL) {
        fprintf(stderr, "FAIL svd wide residual %g\n", rel);
        g_fail = 1;
    }

    if (luma_baseline_truncated_svd(xt, 4, 3, 0, u, s, vt) != LUMA_ERR_ARG)
        g_fail = 1, fprintf(stderr, "FAIL svd r=0\n");
}

int main(void)
{
    test_ternary();
    test_pow2_block();
    test_svd_full_rank();
    if (g_fail) {
        fprintf(stderr, "test_luma_baseline FAILED\n");
        return 1;
    }
    printf("test_luma_baseline OK\n");
    return 0;
}
