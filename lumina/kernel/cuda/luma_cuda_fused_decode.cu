/**
 * @file luma_cuda_fused_decode.cu
 * @brief 融合单 token decode（有损基线骨架）。
 *
 * 注意力 = 低秩背景（r）+ 尾部精确 KV（T）。对照实验，非产品 Enc/Dec。
 * 并行：grid=heads；token 维在线 softmax 串行（依赖前缀 max）。
 */
#include "luma_cuda.h"
#include "luma_cuda_device.h"

#include <math.h>

/** 单输出 GEMV 点积；拆 j/i 嵌套以过循环门禁。 */
__device__ float luma_cuda_fused_decode_dot_w(const __half *W, const __half *x, int h, int d, int j)
{
    int i;
    float acc = 0.0f;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < d; ++i) {
        float xi = __half2float(x[h * d + i]);

        /* W 行主序 [heads,d_out,d_in]；j 为输出通道。 */
        acc += __half2float(W[(size_t)h * d * d + (size_t)j * d + i]) * xi;
    }
    return acc;
}

/** 并行写 q/k/v/acc；W* 布局 [heads,d_out,d_in]。 */
__device__ void luma_cuda_fused_decode_gemv_qkv(const __half *x, const __half *Wq, const __half *Wk,
                                         const __half *Wv, int h, int d, int tid, int nthreads,
                                         float *q, float *k, float *v, float *acc)
{
    int j;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = tid; j < d; j += nthreads) {
        q[j] = luma_cuda_fused_decode_dot_w(Wq, x, h, d, j);
        k[j] = luma_cuda_fused_decode_dot_w(Wk, x, h, d, j);
        v[j] = luma_cuda_fused_decode_dot_w(Wv, x, h, d, j);
        acc[j] = 0.0f; /* 在线 softmax 累加器清零。 */
    }
}

/** 成对 RoPE；偶数 d 由启动器强制。 */
__device__ void luma_cuda_fused_decode_rope(float *q, float *k, int half, int tid, int nthreads,
                                     const float *cos_q, const float *sin_q,
                                     const float *cos_k, const float *sin_k)
{
    int i;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = tid; i < half; i += nthreads) {
        float q0 = q[i], q1 = q[i + half];
        float k0 = k[i], k1 = k[i + half];

        /* 标准 2D 旋转：(x0,x1)←(x0 c - x1 s, x0 s + x1 c)；q/k 可不同相位。 */
        q[i] = q0 * cos_q[i] - q1 * sin_q[i];
        q[i + half] = q0 * sin_q[i] + q1 * cos_q[i];
        k[i] = k0 * cos_k[i] - k1 * sin_k[i];
        k[i + half] = k0 * sin_k[i] + k1 * cos_k[i];
    }
}

/** 部分点积写入 red[tid]，供块归约。 */
__device__ void luma_cuda_fused_decode_partial_dot(float *red, const float *q, const __half *vec,
                                            int d, int tid, int nthreads)
{
    int j;

    red[tid] = 0.0f;
    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = tid; j < d; j += nthreads)
        red[tid] += q[j] * __half2float(vec[j]);
}

/** 在线 softmax 重标定后累加 V。 */
__device__ void luma_cuda_fused_decode_acc_update(float *acc, const __half *vec, float rescale,
                                           float ww, int d, int tid, int nthreads)
{
    int j;

    /* acc ← rescale·acc + w·v：max 更新时旧指数权重整体乘 e^{m_old-m_new}。 */
    for (j = tid; j < d; j += nthreads)
        acc[j] = acc[j] * rescale + ww * __half2float(vec[j]);
}

/** 单 token 注意力步：score → gate → acc（依赖前缀 max）。 */
__device__ void luma_cuda_fused_decode_attn_step(float *q, float *acc, float *red, float *st,
                                          const __half *Vt_r, const float *S_r,
                                          const __half *V_code, const __half *k_tail,
                                          const __half *v_tail, int i, int r, int d,
                                          float scale, int tid, int nthreads)
{
    float sdot, m, ww, rescale;
    /* i<r：低秩码本方向；否则精确尾部 KV。 */
    const __half *vec = (i < r) ? (V_code + i * d) : (v_tail + (i - r) * d);
    const __half *key = (i < r) ? (Vt_r + i * d) : (k_tail + (i - r) * d);

    luma_cuda_fused_decode_partial_dot(red, q, key, d, tid, nthreads);
    /* 块内同步：共享内存读写屏障。 */
    __syncthreads();
    sdot = luma_cuda_block_reduce_sum(red, tid, nthreads);
    if (i < r)
        sdot *= S_r[i]; /* 低秩奇异值加权，与截断 SVD 背景一致。 */
    sdot *= scale;
    __syncthreads(); /* 与后续 st[] 更新分隔，避免与归约缓冲别名混淆。 */

    m = st[0];
    rescale = 1.0f;
    if (sdot > m) {
        /* 新 max：旧权重乘 e^{m-sdot}，保持 Σe^{s-m} 数值稳定。 */
        rescale = expf(m - sdot);
        m = sdot;
    }
    ww = expf(sdot - m);
    if (tid == 0) {
        st[0] = m;
        st[1] = st[1] * rescale + ww; /* 在线归一化分母。 */
    }
    luma_cuda_fused_decode_acc_update(acc, vec, rescale, ww, d, tid, nthreads);
    __syncthreads(); /* 下一 token 步前 st/acc 必须一致。 */
}

/** token 维串行：前缀 max 不可并行。 */
__device__ void luma_cuda_fused_decode_attn_loop(float *q, float *acc, float *red, float *st,
                                          const __half *Vt_r, const float *S_r,
                                          const __half *V_code, const __half *k_tail,
                                          const __half *v_tail, int r, int T, int d,
                                          float scale, int tid, int nthreads)
{
    int i;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < r + T; ++i)
        luma_cuda_fused_decode_attn_step(q, acc, red, st, Vt_r, S_r, V_code, k_tail, v_tail,
                                   i, r, d, scale, tid, nthreads);
}

/** norm==0 时置零，避免除零。 */
__device__ void luma_cuda_fused_decode_normalize(float *acc, float *st, int d, int tid, int nthreads)
{
    int j;
    /* st[1]=0 或非有限：整头输出置零，禁止 Inf 传播。 */
    float inv = (st[1] > 0.0f && isfinite(st[1])) ? (1.0f / st[1]) : 0.0f;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = tid; j < d; j += nthreads)
        acc[j] *= inv;
}

/** Wo 投影单行点积。 */
__device__ float luma_cuda_fused_decode_dot_wo(const __half *Wo, const float *acc, int h, int d, int j)
{
    int i;
    float o = 0.0f;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (i = 0; i < d; ++i)
        o += __half2float(Wo[(size_t)h * d * d + (size_t)j * d + i]) * acc[i];
    return o;
}

/** 并行写 out。 */
__device__ void luma_cuda_fused_decode_proj_out(const __half *Wo, const float *acc, __half *out,
                                         int h, int d, int tid, int nthreads)
{
    int j;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (j = tid; j < d; j += nthreads)
        out[h * d + j] = __float2half(luma_cuda_fused_decode_dot_wo(Wo, acc, h, d, j));
}

/* 设备入口：共享内存布局见文件头。 */
__global__ void luma_cuda_fused_decode_kernel(
    const __half *__restrict__ x,
    const __half *__restrict__ Wq, const __half *__restrict__ Wk,
    const __half *__restrict__ Wv, const __half *__restrict__ Wo,
    const __half *__restrict__ Vt_r, const float *__restrict__ S_r,
    const __half *__restrict__ V_code,
    const __half *__restrict__ k_tail, const __half *__restrict__ v_tail,
    const float *__restrict__ cos_q, const float *__restrict__ sin_q,
    const float *__restrict__ cos_k, const float *__restrict__ sin_k,
    int d, int r, int T, float scale,
    __half *__restrict__ out)
{
    /* 动态共享：块内 q/k/v/acc/red/st 连续布局，避免全局往返。 */
    extern __shared__ float sm[];
    /* 布局：[q|k|v|acc|red|st]；st 紧跟 red，容量含 +3 余量。 */
    float *q = sm;
    float *k = sm + d;
    float *v = sm + 2 * d;
    float *acc = sm + 3 * d;
    float *red = sm + 4 * d;
    float *st = red + blockDim.x;
    int h = blockIdx.x;
    int tid = threadIdx.x;
    int nthreads = blockDim.x;

    luma_cuda_fused_decode_gemv_qkv(x, Wq, Wk, Wv, h, d, tid, nthreads, q, k, v, acc);
    __syncthreads(); /* RoPE 读 q/k 前须完成 GEMV。 */
    luma_cuda_fused_decode_rope(q, k, d / 2, tid, nthreads, cos_q, sin_q, cos_k, sin_k);
    if (tid == 0) {
        st[0] = -INFINITY; /* 在线 max 初值。 */
        st[1] = 0.0f;      /* 在线 Σe^{s-m}。 */
    }
    /* 块内同步：共享内存读写屏障。 */
    __syncthreads();
    luma_cuda_fused_decode_attn_loop(q, acc, red, st, Vt_r, S_r, V_code, k_tail, v_tail,
                               r, T, d, scale, tid, nthreads);
    luma_cuda_fused_decode_normalize(acc, st, d, tid, nthreads);
    __syncthreads(); /* 投影读 acc 前归一化完成。 */
    luma_cuda_fused_decode_proj_out(Wo, acc, out, h, d, tid, nthreads);
}

/* 主机启动器：参数包校验偶数 d 与 head-dim 上限。 */
extern "C" int luma_cuda_fused_decode(const luma_cuda_fused_decode_args_t *args)
{
    size_t shmem;
    int rc;

    if (!args)
        return LUMA_ERR_ARG;
    rc = luma_cuda_launch_validate(
        args->threads_per_block,
        args->x && args->Wq && args->Wk && args->Wv && args->Wo && args->Vt_r &&
            args->S_r && args->V_code && args->k_tail && args->v_tail && args->cos_q &&
            args->sin_q && args->cos_k && args->sin_k && args->out);
    if (rc != LUMA_OK)
        return rc;
    /* d 奇数时 RoPE 成对下标越界。 */
    if (args->heads <= 0 || args->d <= 0 || args->r < 0 || args->T < 0 ||
        (args->d & 1) != 0)
        return LUMA_ERR_ARG;
    if (args->d > LUMA_CUDA_MAX_HEAD_DIM)
        return LUMA_ERR_UNSUPPORTED;

    /* 4*d 向量 + 归约槽 + st[2] 与对齐余量。 */
    shmem = sizeof(float) * ((size_t)args->d * 4u + (size_t)args->threads_per_block + 3u);
    luma_cuda_fused_decode_kernel<<<args->heads, args->threads_per_block, shmem,
                                    args->stream>>>(
        args->x, args->Wq, args->Wk, args->Wv, args->Wo, args->Vt_r, args->S_r,
        args->V_code, args->k_tail, args->v_tail, args->cos_q, args->sin_q, args->cos_k,
        args->sin_k, args->d, args->r, args->T, args->scale, args->out);
    if (cudaGetLastError() != cudaSuccess)
        return LUMA_ERR_CUDA;
    return LUMA_OK;
}
