/* luma_kernels.h — Luminas 内核稳定 C-ABI（绑定层唯一允许调用的头文件）。
 *
 * 分层（LUM-ARC-101 Phase B 已生效）：
 *   错误码 / 产品无损 KV 契约  见 ../algorithm/luma_kv.h（本头 include 之）
 *   基线路径  luma_baseline_*   有损对照（量化 / 截断 SVD），禁止当产品核
 *
 * 约定：
 *   - 返回 int 错误码，不写 errno。
 *   - 浮点路径遵循 IEEE 754；非有限输入返回 LUMA_ERR_NUMERIC。
 *   - 调用方分配全部输出缓冲；本 ABI 不做隐式扩容。
 *   - 输入输出缓冲不得重叠（不支持原地）。
 *   - pybind11 只做编组，不得在绑定里写数值算法。
 */
#ifndef LUMA_KERNELS_H
#define LUMA_KERNELS_H

#include "luma_kv.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Jacobi 特征分解的最大 Gram 边长。更大应走外部 LAPACK，不在本基线里硬撑。 */
#define LUMA_BASELINE_JACOBI_MAX_DIM 512
/* 1<<(mbits+1) 必须落在 float 安全移位内，禁止 >= 24。 */
#define LUMA_POW2_BLOCK_MAX_MANTISSA_BITS 23

/* 数值容差（具名化，禁止在函数体内散落裸数字）。 */
#define LUMA_TERNARY_NEAR_ZERO_SCALE 1e-12f /* |scale| 近零视为全零，避免除零/假阈值 */
#define LUMA_JACOBI_CONVERGE_TOL 1e-24      /* 非对角平方和收敛阈值（相对对角） */
#define LUMA_JACOBI_DIVERGE_TOL 1e-20       /* 超 sweep 仍发散的判定阈值（相对对角） */
#define LUMA_JACOBI_ROTATE_EPS 1e-15        /* 微小旋转跳过阈值 |apq| */
#define LUMA_SVD_SINGULAR_EPS 1e-15         /* 奇异值除零保护 */

/* ---- 基线路径：有损对照，不得当作无损 KV ------------------------------- */

/* 三值权重量化 w ≈ scale * codes, codes∈{-1,0,+1}。
 * scale = mean(|w|)；阈值为 threshold * scale（相对）。
 * 权重域基线，不是 KV 压缩。
 *
 * threshold >= 0 且有限；n==0 时 *scale=0。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_baseline_ternary_encode(const float *w, long n, float threshold,
                                 float *scale, signed char *codes);

/* 块共享 2 的幂次尺度量化（非 OCP MXFP 规范实现）。
 * 每块共享 2 的幂次尺度，再对尾数做 away-from-zero 定点取整。
 *
 * mantissa_bits ∈ [0, LUMA_POW2_BLOCK_MAX_MANTISSA_BITS]；block_size > 0。
 * 末块可短于 block_size。有损：不得套用 2-ulp 无损门。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_baseline_pow2_block_quant(const float *x, long n, int mantissa_bits,
                             int block_size, float *out);

/* 截断 SVD：X(m×n, 行主序) ≈ U(m×r) diag(S) Vt(r×n)。
 * 高矩阵走 XᵀX，宽矩阵走 XXᵀ，避免不必要的大 Gram。
 * r∈[1, min(m,n)]。满秩时应能以小残差重构 X；r < min(m,n) 必然有损。
 *
 * 调用方分配 U/S/Vt。dim=min(m,n) 不得超过 LUMA_BASELINE_JACOBI_MAX_DIM。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NOMEM | LUMA_ERR_NUMERIC | LUMA_ERR_UNSUPPORTED
 */
int luma_baseline_truncated_svd(const double *x, int m, int n, int r,
                                double *u, double *s, double *vt);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_KERNELS_H */
