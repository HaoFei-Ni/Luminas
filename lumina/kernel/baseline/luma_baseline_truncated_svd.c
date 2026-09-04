/* luma_baseline_truncated_svd.c — Gram + Jacobi 截断 SVD（有损基线）。
 *
 * X ≈ U diag(S) Vt。满秩时应重构；截断必然有损，文件名禁止再叫 lossless。
 *
 * 算法：
 *   高矩阵 (m>=n)：G = XᵀX (n×n)，右奇异向量来自 G 的特征向量，
 *                 U = X V S^{-1}。
 *   宽矩阵 (m<n)： G = XXᵀ (m×m)，左奇异向量来自 G，
 *                 Vt = S^{-1} Uᵀ X。
 *
 * Jacobi 必须做一次相似变换 A ← Jᵀ A J。禁止「先转列再转行」的原地双乘
 *（旧实现的正确性缺陷）。
 */
#include "luma_kernels.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

/* 对称特征值：破坏输入 a，特征向量写入 v（列），特征值写入 e。
 * 收敛：严格上三角平方和相对对角足够小。超 sweep 仍发散则 LUMA_ERR_NUMERIC。 */
static int luma_jacobi_sym_eig(double *a, int n, double *v, double *e, int max_sweeps)
{
    int i, p, q, sweep;
    double off, diag_ss;

    memset(v, 0, (size_t)n * (size_t)n * sizeof(double));
    for (i = 0; i < n; ++i)
        v[i * n + i] = 1.0;

    for (sweep = 0; sweep < max_sweeps; ++sweep) {
        off = 0.0;
        diag_ss = 0.0;
        for (p = 0; p < n; ++p) {
            diag_ss += a[p * n + p] * a[p * n + p];
            for (q = p + 1; q < n; ++q)
                off += a[p * n + q] * a[p * n + q];
        }
        /* 相对容差，避免全零矩阵被误判为未收敛。 */
        if (off <= LUMA_JACOBI_CONVERGE_TOL * (1.0 + diag_ss))
            break;

        for (p = 0; p < n - 1; ++p) {
            for (q = p + 1; q < n; ++q) {
                /* 对称化，抑制浮点破坏 A=Aᵀ。 */
                double apq = 0.5 * (a[p * n + q] + a[q * n + p]);
                double app, aqq, tau, t, c, s, npp, nqq;

                if (fabs(apq) < LUMA_JACOBI_ROTATE_EPS)
                    continue;
                app = a[p * n + p];
                aqq = a[q * n + q];
                /* 稳定的 tan(θ/2) 公式，避免 θ→∞。 */
                tau = (aqq - app) / (2.0 * apq);
                t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(tau * tau + 1.0));
                c = 1.0 / sqrt(t * t + 1.0);
                s = t * c;

                /* 非 2×2 块：一次写出对称的新 (p,q) 列/行。 */
                for (i = 0; i < n; ++i) {
                    double aip, aiq, nip, niq;

                    if (i == p || i == q)
                        continue;
                    aip = 0.5 * (a[i * n + p] + a[p * n + i]);
                    aiq = 0.5 * (a[i * n + q] + a[q * n + i]);
                    nip = c * aip - s * aiq;
                    niq = s * aip + c * aiq;
                    a[i * n + p] = a[p * n + i] = nip;
                    a[i * n + q] = a[q * n + i] = niq;
                }

                /* 2×2 对角显式更新，非对角置零（理想 Jacobi 步）。 */
                npp = c * c * app - 2.0 * s * c * apq + s * s * aqq;
                nqq = s * s * app + 2.0 * s * c * apq + c * c * aqq;
                a[p * n + p] = npp;
                a[q * n + q] = nqq;
                a[p * n + q] = a[q * n + p] = 0.0;

                /* V ← V J，只转一次，与 A 的相似变换一致。 */
                for (i = 0; i < n; ++i) {
                    double vip = v[i * n + p];
                    double viq = v[i * n + q];
                    v[i * n + p] = c * vip - s * viq;
                    v[i * n + q] = s * vip + c * viq;
                }
            }
        }
    }

    for (i = 0; i < n; ++i)
        e[i] = a[i * n + i];

    if (sweep >= max_sweeps) {
        off = 0.0;
        diag_ss = 0.0;
        for (p = 0; p < n; ++p) {
            diag_ss += a[p * n + p] * a[p * n + p];
            for (q = p + 1; q < n; ++q)
                off += a[p * n + q] * a[p * n + q];
        }
        if (off > LUMA_JACOBI_DIVERGE_TOL * (1.0 + diag_ss))
            return LUMA_ERR_NUMERIC;
    }
    return LUMA_OK;
}

/* 按下标把特征值从大到小排序（选择排序，dim 很小）。 */
static void luma_sort_desc(const double *e, int n, int *idx)
{
    int i, j;

    for (i = 0; i < n; ++i)
        idx[i] = i;
    for (i = 0; i < n - 1; ++i) {
        int best = i;
        for (j = i + 1; j < n; ++j)
            if (e[idx[j]] > e[idx[best]])
                best = j;
        if (best != i) {
            int tmp = idx[i];
            idx[i] = idx[best];
            idx[best] = tmp;
        }
    }
}

/* G = XᵀX。只累加上三角再镜像，并跳过零元。 */
static void luma_gram_ata(const double *x, int m, int n, double *g)
{
    int i, p, q;

    memset(g, 0, (size_t)n * (size_t)n * sizeof(double));
    for (i = 0; i < m; ++i) {
        const double *row = x + (size_t)i * (size_t)n;
        for (p = 0; p < n; ++p) {
            double xp = row[p];
            double *gp = g + (size_t)p * (size_t)n;
            if (xp == 0.0)
                continue;
            for (q = p; q < n; ++q)
                gp[q] += xp * row[q];
        }
    }
    for (p = 0; p < n; ++p)
        for (q = 0; q < p; ++q)
            g[p * n + q] = g[q * n + p];
}

/* G = XXᵀ，宽矩阵路径。 */
static void luma_gram_aat(const double *x, int m, int n, double *g)
{
    int i, j, k;

    memset(g, 0, (size_t)m * (size_t)m * sizeof(double));
    for (i = 0; i < m; ++i) {
        const double *ri = x + (size_t)i * (size_t)n;
        for (j = i; j < m; ++j) {
            const double *rj = x + (size_t)j * (size_t)n;
            double acc = 0.0;
            for (k = 0; k < n; ++k)
                acc += ri[k] * rj[k];
            g[i * m + j] = acc;
            g[j * m + i] = acc;
        }
    }
}

int luma_baseline_truncated_svd(const double *x, int m, int n, int r,
                                double *u, double *s, double *vt)
{
    int dim, rc, j, k, i;
    int *idx = NULL;
    double *g = NULL, *v = NULL, *e = NULL;

    if (!x || !u || !s || !vt || m <= 0 || n <= 0 || r <= 0 || r > m || r > n)
        return LUMA_ERR_ARG;

    /* P5：脏输入直接拒绝，不要把 NaN 喂给 Jacobi。 */
    for (i = 0; i < m; ++i)
        for (k = 0; k < n; ++k)
            if (!isfinite(x[(size_t)i * (size_t)n + k]))
                return LUMA_ERR_NUMERIC;

    dim = (m >= n) ? n : m;
    if (dim > LUMA_BASELINE_JACOBI_MAX_DIM)
        return LUMA_ERR_UNSUPPORTED;

    g = (double *)calloc((size_t)dim * (size_t)dim, sizeof(double));
    v = (double *)calloc((size_t)dim * (size_t)dim, sizeof(double));
    e = (double *)calloc((size_t)dim, sizeof(double));
    idx = (int *)malloc((size_t)dim * sizeof(int));
    if (!g || !v || !e || !idx) {
        free(g);
        free(v);
        free(e);
        free(idx);
        return LUMA_ERR_NOMEM;
    }

    if (m >= n)
        luma_gram_ata(x, m, n, g);
    else
        luma_gram_aat(x, m, n, g);

    /* sweep 随维数增加；下限 128，避免极小矩阵过早停。 */
    rc = luma_jacobi_sym_eig(g, dim, v, e, dim * 8 < 128 ? 128 : dim * 8);
    if (rc != LUMA_OK) {
        free(g);
        free(v);
        free(e);
        free(idx);
        return rc;
    }

    luma_sort_desc(e, dim, idx);
    for (j = 0; j < r; ++j) {
        /* Gram 特征值理论上 ≥0；负值视为数值噪声并钳零。 */
        double lam = e[idx[j]] > 0.0 ? e[idx[j]] : 0.0;
        s[j] = sqrt(lam);
    }

    if (m >= n) {
        /* Vt 的第 j 行 = 第 idx[j] 个右特征向量。 */
        for (j = 0; j < r; ++j) {
            int col = idx[j];
            for (k = 0; k < n; ++k)
                vt[j * n + k] = v[k * n + col];
        }
        /* U = X V S^{+}，小奇异值置零以免除零放大。 */
        for (i = 0; i < m; ++i) {
            const double *row = x + (size_t)i * (size_t)n;
            for (j = 0; j < r; ++j) {
                double acc = 0.0;
                for (k = 0; k < n; ++k)
                    acc += row[k] * vt[j * n + k];
                u[i * r + j] = (s[j] > LUMA_SVD_SINGULAR_EPS) ? acc / s[j] : 0.0;
            }
        }
    } else {
        for (i = 0; i < m; ++i)
            for (j = 0; j < r; ++j)
                u[i * r + j] = v[i * m + idx[j]];
        for (j = 0; j < r; ++j) {
            for (k = 0; k < n; ++k) {
                double acc = 0.0;
                for (i = 0; i < m; ++i)
                    acc += u[i * r + j] * x[(size_t)i * (size_t)n + k];
                vt[j * n + k] = (s[j] > LUMA_SVD_SINGULAR_EPS) ? acc / s[j] : 0.0;
            }
        }
    }

    free(g);
    free(v);
    free(e);
    free(idx);
    return LUMA_OK;
}
