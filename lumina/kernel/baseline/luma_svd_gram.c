/**
 * @file luma_svd_gram.c
 * @brief XᵀX / XXᵀ Gram（截断 SVD 私有）。
 *
 * 仅累加上三角再镜像；零元跳过。点积走 luma_math_dot_f64。
 */
#include "baseline/luma_svd.h"

#include <string.h>

/** 固定行、固定 p：累加 q≥p，利用对称性减半写。 */
static void luma_svd_gram_xt_x_add_p(const double *row, int n, int p, double *g)
{
    int q;
    double xp = row[p];
    double *gp = g + (size_t)p * (size_t)n;

    if (xp == 0.0)
        return; /* 稀疏/零元短路，避免空乘。 */
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (q = p; q < n; ++q)
        gp[q] += xp * row[q];
}

/** 单行对 G 的外积累加；拆开 i/p 嵌套。 */
static void luma_svd_gram_xt_x_row(const double *row, int n, double *g)
{
    int p;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (p = 0; p < n; ++p)
        luma_svd_gram_xt_x_add_p(row, n, p, g);
}

/** 上三角镜像到下三角，保持对称 Jacobi 输入。 */
static void luma_svd_gram_mirror_row(double *g, int n, int p)
{
    int q;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (q = 0; q < p; ++q)
        g[p * n + q] = g[q * n + p];
}

/* G = XᵀX（高矩阵路径）；n×n，避免显式形成 m×m。 */
void luma_svd_gram_xt_x(const double *x, int m, int n, double *g)
{
    int i, p;

    memset(g, 0, (size_t)n * (size_t)n * sizeof(double));
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < m; ++i)
        luma_svd_gram_xt_x_row(x + (size_t)i * (size_t)n, n, g);
    /* 镜像在全部行累加完成后一次完成，避免中途破坏上三角约定。 */
    for (p = 0; p < n; ++p)
        luma_svd_gram_mirror_row(g, n, p);
}

/** 固定 i 填 G[i,j] j≥i（宽矩阵 XXᵀ）。 */
static void luma_svd_gram_x_xt_fill_row(const double *x, int m, int n, int i, double *g)
{
    int j;
    const double *ri = x + (size_t)i * (size_t)n;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = i; j < m; ++j) {
        double acc = luma_math_dot_f64(ri, x + (size_t)j * (size_t)n, n);

        /* 一次写对称两侧，省去事后镜像扫描。 */
        g[i * m + j] = acc;
        g[j * m + i] = acc;
    }
}

/* G = XXᵀ（宽矩阵路径）；m×m。 */
void luma_svd_gram_x_xt(const double *x, int m, int n, double *g)
{
    int i;

    memset(g, 0, (size_t)m * (size_t)m * sizeof(double));
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < m; ++i)
        luma_svd_gram_x_xt_fill_row(x, m, n, i, g);
}
