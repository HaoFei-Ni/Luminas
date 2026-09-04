/**
 * @file luma_cuda_kv_quant_int8.cu
 * @brief 每块 int8 KV 量化（有损 GPU 基线）。
 *
 * 一 block ↔ 一量化块：shared 归约 amax → scale=2^{floor(log2(amax))} → 饱和量化。
 */
#include "luma_cuda.h"
#include "luma_cuda_util.h"

#include <math.h>

/** Thread-strided local amax for shared reduce（无别名写冲突）。 */
__device__ float luma_cuda_kv_amax_partial(const __half *x, int start, int end,
                                          int tid, int nthreads)
{
    float local = 0.0f;
    int i;

    /* 步长 = nthreads：各线程写私有 local，避免对同一 smem 槽竞态。 */
    for (i = start + tid; i < end; i += nthreads) {
        float a = fabsf(__half2float(x[i]));

        if (a > local)
            local = a;
    }
    return local;
}

/** 对称饱和到 ±127；避开 -128 以利对称反量化。 */
__device__ void luma_cuda_kv_encode_int8(const __half *x, signed char *codes,
                                        float scale, int start, int end,
                                        int tid, int nthreads)
{
    int i;

    for (i = start + tid; i < end; i += nthreads) {
        float v = __half2float(x[i]) / scale;

        /* clip 到 ±127：int8 对称动态范围，避免 -128 无正侧配对。 */
        codes[i] = (signed char)rintf(fminf(fmaxf(v, -127.0f), 127.0f));
    }
}

/** 一 CUDA block 对应一量化块：归约尺度后编码。 */
__global__ void luma_cuda_kv_quant_int8_kernel(
    const __half *__restrict__ x,
    signed char *__restrict__ codes,
    float *__restrict__ scales,
    int n,
    int block_size)
{
    extern __shared__ float smem[];
    int block_idx = blockIdx.x;
    int start = block_idx * block_size;
    int end = start + block_size;
    int tid = threadIdx.x;
    int nthreads = blockDim.x;
    float scale;

    if (end > n)
        end = n; /* 末块变短，尺度仍按该短块 amax。 */

    smem[tid] = luma_cuda_kv_amax_partial(x, start, end, tid, nthreads);
    __syncthreads(); /* 归约前必须看见全部局部 amax。 */
    scale = luma_cuda_block_reduce_max(smem, tid, nthreads);
    if (tid == 0) {
        /* 与 CPU pow2_floor 同语义；amax=0 → scale=1，避免除零。 */
        scale = (scale > 0.0f) ? exp2f(floorf(log2f(scale))) : 1.0f;
        scales[block_idx] = scale;
        smem[0] = scale; /* 广播槽：全体线程下一拍读同一尺度。 */
    }
    __syncthreads(); /* 等 tid0 写完 smem[0] 再编码。 */
    scale = smem[0];
    luma_cuda_kv_encode_int8(x, codes, scale, start, end, tid, nthreads);
}

/* 主机启动器：线程数须为 2 的幂；检查 cudaGetLastError。 */
extern "C" int luma_cuda_kv_quant_int8(
    const __half *x, signed char *codes, float *scales,
    int n, int block_size, int threads_per_block, cudaStream_t stream)
{
    int num_blocks;
    size_t shmem;
    int rc;

    rc = luma_cuda_launch_validate(threads_per_block, x && codes && scales && n > 0 &&
                                                          block_size > 0);
    if (rc != LUMA_OK)
        return rc;

    num_blocks = (n + block_size - 1) / block_size;
    shmem = sizeof(float) * (size_t)threads_per_block;
    luma_cuda_kv_quant_int8_kernel<<<num_blocks, threads_per_block, shmem, stream>>>(
        x, codes, scales, n, block_size);
    if (cudaGetLastError() != cudaSuccess)
        return LUMA_ERR_CUDA;
    return LUMA_OK;
}
