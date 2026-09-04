/**
 * @file luma_svd_truncated.c
 * @brief 截断 SVD 驱动：X ≈ U diag(S) Vt（有损基线）。
 *
 * 高矩阵：G=XᵀX；宽矩阵：G=XXᵀ。子模块：luma_svd_{gram,jacobi}；原语：luma_math。
 */
#include "baseline/luma_svd.h"
#include "luma_kernel.h"

#include <math.h>
#include <stdlib.h>

/** 统一释放：alloc 失败与 eig 失败共用，避免泄漏分叉。 */
static void luma_svd_work_free(double *g, double *v, double *e, int *idx)
{
    free(g);
    free(v);
    free(e);
    free(idx);
}

/** 工作区一次申请；任一失败则全回滚。 */
static int luma_svd_work_alloc(int dim, double **g, double **v, double **e, int **idx)
{
    *g = (double *)calloc((size_t)dim * (size_t)dim, sizeof(double));
    *v = (double *)calloc((size_t)dim * (size_t)dim, sizeof(double));
    *e = (double *)calloc((size_t)dim, sizeof(double));
    *idx = (int *)malloc((size_t)dim * sizeof(int));
    if (!*g || !*v || !*e || !*idx) {
        luma_svd_work_free(*g, *v, *e, *idx);
        *g = *v = *e = NULL;
        *idx = NULL;
        return LUMA_ERR_NOMEM;
    }
    return LUMA_OK;
}

/** λ→σ：负特征值钳到 0（数值噪声），再开方。 */
static void luma_svd_fill_singular(const double *e, const int *idx, int r, double *s)
{
    int j;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = 0; j < r; ++j) {
        /* Gram 特征值应 ≥0；微小负值来自舍入，钳零后再 √。 */
        double lam = e[idx[j]] > 0.0 ? e[idx[j]] : 0.0;

        s[j] = sqrt(lam);
    }
}

/** 从 V 列拷到 Vt 行：高矩阵右奇异向量。 */
static void luma_svd_copy_vt_row(const double *v, int n, int col, double *vt_row)
{
    int k;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (k = 0; k < n; ++k)
        vt_row[k] = v[k * n + col];
}

/** U 行：X 行 · Vt / σ；σ≈0 置零防除零放大。 */
static void luma_svd_u_from_row(const double *row, const double *vt, const double *s,
                               int n, int r, double *u_row)
{
    int j;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = 0; j < r; ++j) {
        double acc = luma_math_dot_f64(row, vt + (size_t)j * (size_t)n, n);

        /* σ≈0：对应方向无信息，置 0 而非 1/σ 爆炸。 */
        u_row[j] = (s[j] > LUMA_SVD_SINGULAR_EPS) ? acc / s[j] : 0.0;
    }
}

/** 高矩阵组装：先 Vt 后 U=X V Σ⁻¹。 */
static void luma_svd_assemble_tall(const double *x, const double *v, const int *idx,
                                   const double *s, int m, int n, int r,
                                   double *u, double *vt)
{
    int i, j;

    /* 先写 Vt，使 U 行可复用已排好的右奇异向量。 */
    for (j = 0; j < r; ++j)
        luma_svd_copy_vt_row(v, n, idx[j], vt + (size_t)j * (size_t)n);
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < m; ++i)
        luma_svd_u_from_row(x + (size_t)i * (size_t)n, vt, s, n, r,
                            u + (size_t)i * (size_t)r);
}

/** 宽矩阵：U 取自 G 的特征向量列重排。 */
static void luma_svd_copy_u_row(const double *v, const int *idx, int m, int r, int i,
                               double *u_row)
{
    int j;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = 0; j < r; ++j)
        u_row[j] = v[i * m + idx[j]];
}

/** Vt 元素：u[:,j]·X[:,k]；拆开 j/k/i 三层。 */
static double luma_svd_col_dot_u(const double *u, const double *x, int m, int n, int r,
                                int j, int k)
{
    int i;
    double acc = 0.0;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < m; ++i)
        acc += u[i * r + j] * x[(size_t)i * (size_t)n + (size_t)k];
    return acc;
}

/** 宽矩阵 Vt 行：Σ⁻¹ Uᵀ X。 */
static void luma_svd_vt_from_u(const double *u, const double *x, const double *s,
                              int m, int n, int r, int j, double *vt_row)
{
    int k;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (k = 0; k < n; ++k) {
        double acc = luma_svd_col_dot_u(u, x, m, n, r, j, k);

        vt_row[k] = (s[j] > LUMA_SVD_SINGULAR_EPS) ? acc / s[j] : 0.0;
    }
}

/** 宽矩阵组装入口。 */
static void luma_svd_assemble_wide(const double *x, const double *v, const int *idx,
                                   const double *s, int m, int n, int r,
                                   double *u, double *vt)
{
    int i, j;

    /* XXᵀ 特征向量在左奇异空间，故先 U 后 Vt。 */
    for (i = 0; i < m; ++i)
        luma_svd_copy_u_row(v, idx, m, r, i, u + (size_t)i * (size_t)r);
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = 0; j < r; ++j)
        luma_svd_vt_from_u(u, x, s, m, n, r, j, vt + (size_t)j * (size_t)n);
}

/* 导出截断 SVD：拒绝重叠缓冲；r 截断必然有损。 */
int luma_svd_truncated(const double *x, double *u, double *s, double *vt,
                       int m, int n, int r)
{
    int dim, rc;
    int *idx = NULL;
    double *g = NULL, *v = NULL, *e = NULL;

    if (!x || !u || !s || !vt || m <= 0 || n <= 0 || r <= 0 || r > m || r > n)
        return LUMA_ERR_ARG;
    /* 原地写 U/Vt 会破坏尚未读完的 X，别名未定义。 */
    if (luma_math_ptr_ranges_overlap(x, (size_t)m * (size_t)n * sizeof(double),
                                     u, (size_t)m * (size_t)r * sizeof(double)) ||
        luma_math_ptr_ranges_overlap(x, (size_t)m * (size_t)n * sizeof(double),
                                     vt, (size_t)r * (size_t)n * sizeof(double)))
        return LUMA_ERR_ARG;

    rc = luma_math_require_finite_f64(x, (long)m * (long)n);
    if (rc != LUMA_OK)
        return rc;

    dim = (m >= n) ? n : m;
    if (dim > LUMA_JACOBI_MAX_DIM)
        return LUMA_ERR_UNSUPPORTED;

    rc = luma_svd_work_alloc(dim, &g, &v, &e, &idx);
    if (rc != LUMA_OK)
        return rc;

    /* 选较小 Gram：高矩阵 n×n，宽矩阵 m×m，降低 Jacobi 立方代价。 */
    if (m >= n)
        luma_svd_gram_xt_x(x, m, n, g);
    else
        luma_svd_gram_x_xt(x, m, n, g);

    rc = luma_svd_jacobi_sym_eig(g, dim, v, e, luma_svd_jacobi_sweep_budget(dim));
    if (rc != LUMA_OK) {
        luma_svd_work_free(g, v, e, idx);
        return rc;
    }

    luma_svd_argsort_desc(e, dim, idx);
    luma_svd_fill_singular(e, idx, r, s);
    if (m >= n)
        luma_svd_assemble_tall(x, v, idx, s, m, n, r, u, vt);
    else
        luma_svd_assemble_wide(x, v, idx, s, m, n, r, u, vt);

    luma_svd_work_free(g, v, e, idx);
    return LUMA_OK;
}
