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

/* 统一错误码。0 成功；负值失败。绑定层用 luma_strerror 映射异常。 */
typedef enum luma_status_e {
    LUMA_OK = 0,              /* 成功 */
    LUMA_ERR_ARG = -1,        /* 空指针、非法维度、非法超参 */
    LUMA_ERR_NOMEM = -2,      /* calloc/malloc 失败 */
    LUMA_ERR_NUMERIC = -3,    /* NaN/Inf、Jacobi 未收敛等 */
    LUMA_ERR_CUDA = -4,       /* launch 或 runtime API 失败 */
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

#ifdef __cplusplus
}
#endif

#endif /* LUMA_KV_H */
