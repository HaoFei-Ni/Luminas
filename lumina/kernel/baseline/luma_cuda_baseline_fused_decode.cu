/* luma_cuda_baseline_fused_decode.cu — 融合单 token decode（有损基线骨架）。
 *
 * 注意力 = 低秩背景（r 个方向）+ 尾部精确 KV（T）。这是低秩/驱逐对照，
 * 不是 theory/state-cache 的产品 Enc/Dec。
 *
 * 并行：grid=heads，block 内按 d 分片做 GEMV / RoPE / 点积。
 * 在线 softmax 对 token 维串行（算法本身依赖前缀 max）。
 * d 由共享内存承载，超 LUMA_CUDA_MAX_HEAD_DIM 拒掉。
 *
 * 当前 token 的 k/v 只用于占位残差路径；注意力读 V_code / v_tail。
 * 作为对照核，当前 token 不会写回 cache。
 */
#include "luma_cuda_kernels.h"
#include <math.h>

static int luma_is_pow2(int x)
{
    return x > 0 && (x & (x - 1)) == 0;
}

/* 块内求和归约。调用前后调用方负责 syncthreads 边界。 */
__device__ static float luma_reduce_sum(float *red, int tid, int nthreads)
{
    for (int stride = nthreads >> 1; stride > 0; stride >>= 1) {
        if (tid < stride)
            red[tid] += red[tid + stride];
        __syncthreads();
    }
    return red[0];
}

__global__ void luma_cuda_baseline_fused_decode_kernel(
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
    extern __shared__ float sm[];
    /* 布局：q|k|v|acc 各 d，red 为 nthreads，st[0]=m st[1]=norm。 */
    float *q = sm;
    float *k = sm + d;
    float *v = sm + 2 * d;
    float *acc = sm + 3 * d;
    float *red = sm + 4 * d;
    float *st = red + blockDim.x;

    int h = blockIdx.x;
    int tid = threadIdx.x;
    int nthreads = blockDim.x;
    int half = d / 2;
    int j, i;

    /* GEMV：每线程算一组输出维。W* 布局 [heads, d_out, d_in]。 */
    for (j = tid; j < d; j += nthreads) {
        float aq = 0.0f, ak = 0.0f, av = 0.0f;
        for (i = 0; i < d; ++i) {
            float xi = __half2float(x[h * d + i]);
            aq += __half2float(Wq[(size_t)h * d * d + (size_t)j * d + i]) * xi;
            ak += __half2float(Wk[(size_t)h * d * d + (size_t)j * d + i]) * xi;
            av += __half2float(Wv[(size_t)h * d * d + (size_t)j * d + i]) * xi;
        }
        q[j] = aq;
        k[j] = ak;
        v[j] = av; /* 占位残差路径；注意力读 V_code / v_tail。 */
        acc[j] = 0.0f;
    }
    __syncthreads();

    /* RoPE：成对旋转，要求 d 为偶数（启动器已检查）。 */
    for (i = tid; i < half; i += nthreads) {
        float q0 = q[i], q1 = q[i + half];
        float k0 = k[i], k1 = k[i + half];
        q[i] = q0 * cos_q[i] - q1 * sin_q[i];
        q[i + half] = q0 * sin_q[i] + q1 * cos_q[i];
        k[i] = k0 * cos_k[i] - k1 * sin_k[i];
        k[i + half] = k0 * sin_k[i] + k1 * cos_k[i];
    }
    if (tid == 0) {
        st[0] = -INFINITY; /* running max */
        st[1] = 0.0f;      /* running softmax 归一化 */
    }
    __syncthreads();

    /* i < r：低秩背景；之后：尾部精确 token。 */
    for (i = 0; i < r + T; ++i) {
        float sdot = 0.0f;
        float m, ww, rescale;
        const __half *vec = (i < r) ? (V_code + i * d) : (v_tail + (i - r) * d);

        red[tid] = 0.0f;
        if (i < r) {
            for (j = tid; j < d; j += nthreads)
                red[tid] += q[j] * __half2float(Vt_r[i * d + j]);
        } else {
            int t = i - r;
            for (j = tid; j < d; j += nthreads)
                red[tid] += q[j] * __half2float(k_tail[t * d + j]);
        }
        __syncthreads();
        sdot = luma_reduce_sum(red, tid, nthreads);
        if (i < r)
            sdot *= S_r[i];
        sdot *= scale;
        __syncthreads();

        /* 在线 softmax：分数升高则回缩放 acc 与 norm。 */
        m = st[0];
        rescale = 1.0f;
        if (sdot > m) {
            rescale = expf(m - sdot);
            m = sdot;
        }
        ww = expf(sdot - m);
        if (tid == 0) {
            st[0] = m;
            st[1] = st[1] * rescale + ww;
        }
        for (j = tid; j < d; j += nthreads)
            acc[j] = acc[j] * rescale + ww * __half2float(vec[j]);
        __syncthreads();
    }

    {
        /* norm==0 时输出 0，避免除零。 */
        float inv = (st[1] > 0.0f && isfinite(st[1])) ? (1.0f / st[1]) : 0.0f;
        for (j = tid; j < d; j += nthreads)
            acc[j] *= inv;
        __syncthreads();
    }

    for (j = tid; j < d; j += nthreads) {
        float o = 0.0f;
        for (i = 0; i < d; ++i)
            o += __half2float(Wo[(size_t)h * d * d + (size_t)j * d + i]) * acc[i];
        out[h * d + j] = __float2half(o);
    }
}

extern "C" int luma_cuda_baseline_fused_decode(
    const __half *x, const __half *Wq, const __half *Wk, const __half *Wv, const __half *Wo,
    const __half *Vt_r, const float *S_r, const __half *V_code,
    const __half *k_tail, const __half *v_tail,
    const float *cos_q, const float *sin_q, const float *cos_k, const float *sin_k,
    int heads, int d, int r, int T, float scale, int threads_per_block,
    cudaStream_t stream, __half *out)
{
    size_t shmem;

    if (!x || !Wq || !Wk || !Wv || !Wo || !Vt_r || !S_r || !V_code ||
        !k_tail || !v_tail || !cos_q || !sin_q || !cos_k || !sin_k || !out)
        return LUMA_ERR_ARG;
    if (heads <= 0 || d <= 0 || r < 0 || T < 0 || (d & 1) != 0)
        return LUMA_ERR_ARG;
    if (d > LUMA_CUDA_MAX_HEAD_DIM)
        return LUMA_ERR_UNSUPPORTED;
    if (!luma_is_pow2(threads_per_block) || threads_per_block > 1024)
        return LUMA_ERR_ARG;

    shmem = sizeof(float) * ((size_t)d * 4u + (size_t)threads_per_block + 3u);
    luma_cuda_baseline_fused_decode_kernel<<<heads, threads_per_block, shmem, stream>>>(
        x, Wq, Wk, Wv, Wo, Vt_r, S_r, V_code, k_tail, v_tail,
        cos_q, sin_q, cos_k, sin_k, d, r, T, scale, out);
    if (cudaGetLastError() != cudaSuccess)
        return LUMA_ERR_CUDA;
    return LUMA_OK;
}
