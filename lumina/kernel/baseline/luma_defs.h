/**
 * @file luma_defs.h
 * @brief Baseline 公共定义：容差、结构上限、具名常量（目录语义已含 baseline）。
 *
 * @note 错误码体系仍在 algorithm/luma_kv.h（LUMA_OK / LUMA_ERR_*），本头不重复定义。
 *       有损基线专用；禁止当作产品无损 KV 契约。
 */
#ifndef LUMA_DEFS_H
#define LUMA_DEFS_H

#include "luma_kv.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Jacobi / Gram 工作矩阵最大边长；超出应换外部 LAPACK。 */
#define LUMA_JACOBI_MAX_DIM 512

/** 1<<(mbits+1) 须落在 float 安全移位内；禁止 >= 24。 */
#define LUMA_POW2_MAX_MANTISSA_BITS 23

/** |scale| 近零 → 三值码全零，避免假阈值。 */
#define LUMA_TERNARY_NEAR_ZERO 1e-12f

/** 非对角能量 / (1+diag) 收敛门。 */
#define LUMA_JACOBI_CONVERGE_TOL 1e-24

/** sweep 耗尽后仍发散的判定门。 */
#define LUMA_JACOBI_DIVERGE_TOL 1e-20

/** |a_pq| 过小则跳过旋转，抑制无效抖动。 */
#define LUMA_JACOBI_ROTATE_EPS 1e-15

/** σ≈0 时 U/Vt 置零，防止除零放大。 */
#define LUMA_SVD_SINGULAR_EPS 1e-15

/** Jacobi sweep 预算下界（与历史基线对齐）。 */
#define LUMA_JACOBI_SWEEP_FLOOR 128

/** Jacobi sweep 预算系数：sweeps ≈ max(FLOOR, dim*SCALE)。 */
#define LUMA_JACOBI_SWEEP_SCALE 8

/* ---- 兼容旧宏名（下一主版本删除） ------------------------------------ */
#define LUMA_BASELINE_JACOBI_MAX_DIM LUMA_JACOBI_MAX_DIM
#define LUMA_BASELINE_POW2_MAX_MANTISSA_BITS LUMA_POW2_MAX_MANTISSA_BITS
#define LUMA_BASELINE_TERNARY_NEAR_ZERO LUMA_TERNARY_NEAR_ZERO
#define LUMA_BASELINE_JACOBI_CONVERGE_TOL LUMA_JACOBI_CONVERGE_TOL
#define LUMA_BASELINE_JACOBI_DIVERGE_TOL LUMA_JACOBI_DIVERGE_TOL
#define LUMA_BASELINE_JACOBI_ROTATE_EPS LUMA_JACOBI_ROTATE_EPS
#define LUMA_BASELINE_SVD_SINGULAR_EPS LUMA_SVD_SINGULAR_EPS
#define LUMA_POW2_BLOCK_MAX_MANTISSA_BITS LUMA_POW2_MAX_MANTISSA_BITS
#define LUMA_TERNARY_NEAR_ZERO_SCALE LUMA_TERNARY_NEAR_ZERO
#ifdef __cplusplus
}
#endif

#endif /* LUMA_DEFS_H */
