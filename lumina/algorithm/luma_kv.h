/* luma_kv.h — 纯算法层契约（产品无损 KV 的 C-ABI）。
 *
 * 这是 algorithm/ 的自含接口头：错误码 + 错误串 + 产品 Enc/Dec + FP64 预言机。
 * 不依赖 kernel/ 或 wrapper/；只声明，不含任何实现。
 *
 * 分层：platform-agnostic，无系统 API、无 CUDA、无副作用、无全局状态。
 * 约定（同 kernel 命名表）：
 *   - 返回 int 错误码，不写 errno。
 *   - 浮点路径遵循 IEEE 754；非有限输入返回 LUMA_ERR_NUMERIC。
 *   - 调用方分配全部输出缓冲；本 ABI 不做隐式扩容。
 *   - 输入输出缓冲不得重叠（不支持原地）。
 */
#ifndef LUMA_KV_H
#define LUMA_KV_H

#ifdef __cplusplus
extern "C" {
#endif

/* 统一错误码。0 成功；负值失败。绑定层用 luma_strerror 映射异常。
 * 槽位 -4 保留给平台后端（CUDA 等），定义见 kernel/luma_cuda.h 的 LUMA_ERR_CUDA；
 * 本纯算法头不声明平台错误枚举项，避免 algorithm 依赖硬件语义。 */
typedef enum luma_status_e {
    LUMA_OK = 0,              /* 成功 */
    LUMA_ERR_ARG = -1,        /* 空指针、非法维度、非法超参 */
    LUMA_ERR_NOMEM = -2,      /* calloc/malloc 失败 */
    LUMA_ERR_NUMERIC = -3,    /* NaN/Inf、Jacobi 未收敛等 */
    LUMA_ERR_UNSUPPORTED = -5 /* 超出实现上限（维数、头维等） */
} luma_status_t;

/* 将错误码转为稳态英文短句，供日志与 Python 异常使用。未知码返回 "unknown error"。 */
const char *luma_strerror(int rc);

/* FP32 单位舍入（2^-23）。2-ulp 门 = 2 * LUMA_ULP32 * max(1, |S_i|)。 */
#define LUMA_ULP32 1.1920928955078125e-7

/* ---- 产品路径：无损 KV 数值契约（theory P1/P2） ------------------------ */

/* FP64 预言机：逐元复制有限输入。
 * L1/L5 用本函数对照 encode/decode 的重构。将来替换压缩算法时不得改本语义。
 *
 * x, out: 长度 n，允许 n==0（空操作）。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC
 */
int luma_kv_ref_copy_f64(const double *x, long n, double *out);

/* 产品 Enc/Dec（KV-ENC-CANDIDATE-1）：精确 f32 RLE，重构 bit-exact。
 * 实现：luma_kv_encode.c / luma_kv_decode.c。调用方 enc_cap≥2n（n>0）。
 * 2-ulp / 论文 L1：|Ŝ_i-S_i|≤2·2^{-23}·max(1,|S_i|)；无 NaN/Inf。
 * 返回：LUMA_OK | LUMA_ERR_ARG | LUMA_ERR_NUMERIC | LUMA_ERR_UNSUPPORTED
 */
int luma_kv_encode_f32(const float *x, long n, float *enc, long enc_cap, long *enc_len);
/* RLE Dec：消费成对码流，展开后长度必须等于 n。 */
int luma_kv_decode_f32(const float *enc, long enc_len, float *out, long n);

#ifdef __cplusplus
}
#endif

#endif /* LUMA_KV_H */
