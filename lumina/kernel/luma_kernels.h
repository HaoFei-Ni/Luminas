/* luma_kernels.h — Luminas 内核稳定 C-ABI（绑定层唯一允许调用的头文件）。
 *
 * 分层：
 *   产品路径  luma_kv_* / luma_kv_ref_*     无损状态缓存（理论见 theory/state-cache P0–P5）
 *   基线路径  luma_baseline_*               有损对照（量化 / 截断 SVD），禁止当产品核
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

#ifdef __cplusplus
extern "C" {
#endif

/* 统一错误码。0 成功；负值失败。绑定层用 luma_strerror 映射异常。 */
enum {
    LUMA_OK = 0,              /* 成功 */
    LUMA_ERR_ARG = -1,        /* 空指针、非法维度、非法超参 */
    LUMA_ERR_NOMEM = -2,      /* calloc/malloc 失败 */
    LUMA_ERR_NUMERIC = -3,    /* NaN/Inf、Jacobi 未收敛等 */
    LUMA_ERR_CUDA = -4,       /* launch 或 runtime API 失败 */
    LUMA_ERR_UNSUPPORTED = -5 /* 超出实现上限（维数、头维等） */
};

/* Jacobi 特征分解的最大 Gram 边长。更大应走外部 LAPACK，不在本基线里硬撑。 */
#define LUMA_BASELINE_JACOBI_MAX_DIM 512
/* fused-decode 共享内存按此上限分配；超过返回 LUMA_ERR_UNSUPPORTED。 */
#define LUMA_CUDA_MAX_HEAD_DIM 256
/* 1<<(mbits+1) 必须落在 float 安全移位内，禁止 >= 24。 */
#define LUMA_MXFP_MAX_MANTISSA_BITS 23

/* 将错误码转为稳态英文短句，供日志与 Python 异常使用。未知码返回 "unknown error"。 */
const char *luma_strerror(int rc);

/* ---- 产品路径：无损 KV 数值契约（theory P1/P2） ------------------------ */

/* FP64 预言机：逐元复制有限输入。
 * L1/L5 用本函数对照 encode/decode 的重构。将来替换压缩算法时不得改本语义。
 *
 * x, out: 长度 n，允许 n==0（空操作）。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_kv_ref_copy_f64(const double *x, long n, double *out);

/* 候选产品 Enc/Dec。
 *
 * 当前实现是有限性检查后的恒等映射，压缩域长度恒等于 n。
 * 这是 ABI 与测试挂钩，不是发表用压缩器：禁止据此报告压缩比 ρ。
 * 真公式落地时：
 *   - Enc 可把 n 个 float 压成更短的 enc（enc_cap 是容量上界）；
 *   - Dec 把 enc 映回长度 n 的 Ŝ；
 *   - 继续用 luma_kv_ref_copy_f64 做 2-ulp 门（P2）。
 *
 * 2-ulp 门：|Ŝ_i - S_i| <= 2 * 2^{-23} * max(1, |S_i|)，且无 NaN/Inf。
 * 输入输出不得重叠。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_kv_encode_f32(const float *x, long n, float *enc, long enc_cap, long *enc_len);
int luma_kv_decode_f32(const float *enc, long enc_len, float *out, long n);

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

/* MXFP 风格块量化（非 OCP MXFP 规范实现）。
 * 每块共享 2 的幂次尺度，再对尾数做 away-from-zero 定点取整。
 *
 * mantissa_bits ∈ [0, LUMA_MXFP_MAX_MANTISSA_BITS]；block_size > 0。
 * 末块可短于 block_size。有损：不得套用 2-ulp 无损门。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_baseline_mxfp_quant(const float *x, long n, int mantissa_bits,
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
