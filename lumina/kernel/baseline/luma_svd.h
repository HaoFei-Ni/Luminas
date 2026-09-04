/**
 * @file luma_svd.h
 * @brief 截断 SVD 私有契约：Jacobi / Gram（不进公共 C-ABI）。
 *
 * @note 公共入口仅 luma_svd_truncated（见 luma_kernels.h）。
 */
#ifndef LUMA_SVD_H
#define LUMA_SVD_H

#include "baseline/luma_math.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 对称 Jacobi：破坏 a；特征向量列写 v，特征值写 e。
 * @param[in,out] a 对称矩阵，行主序，被相似变换破坏
 * @param[in] n 阶
 * @param[out] v 特征向量列
 * @param[out] e 特征值
 * @param[in] max_sweeps 最大 sweep 数
 * @return LUMA_OK | LUMA_ERR_NUMERIC
 */
int luma_svd_jacobi_sym_eig(double *a, int n, double *v, double *e, int max_sweeps);

/**
 * @brief 与历史基线对齐的 sweep 预算（过小则大维不收敛）。
 * @param[in] dim 矩阵阶
 * @return sweep 上界
 */
int luma_svd_jacobi_sweep_budget(int dim);

/**
 * @brief 特征值降序下标，供截断取最大 r 个分量。
 * @param[in] e 特征值
 * @param[in] n 长度
 * @param[out] idx 排序后的下标
 */
void luma_svd_argsort_desc(const double *e, int n, int *idx);

/**
 * @brief G = XᵀX（高矩阵路径）。
 * @param[in] x 行主序 m×n
 * @param[in] m 行数
 * @param[in] n 列数
 * @param[out] g n×n Gram
 */
void luma_svd_gram_xt_x(const double *x, int m, int n, double *g);

/**
 * @brief G = XXᵀ（宽矩阵路径）。
 * @param[in] x 行主序 m×n
 * @param[in] m 行数
 * @param[in] n 列数
 * @param[out] g m×m Gram
 */
void luma_svd_gram_x_xt(const double *x, int m, int n, double *g);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_SVD_H */
