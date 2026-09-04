/* luma_cuda_baseline_kv_int8.cu — 每块 int8 KV 量化（有损 GPU 基线）。
 *
 * 一个 CUDA block 对应一个量化块。线程跨步扫描该块：
 *   1) shared-memory 归约求 amax；
 *   2) 尺度取 2^{floor(log2(amax))}；
 *   3) 各线程只写自己的 codes[i]，禁止全员重复写同一地址。
 *
 * 这不是无损 KV。绑定层的 H2D 往返会吃掉加速，正式路径应传入设备指针。
 */
#include "luma_cuda_kernels.h"
#include "luma_cuda_util.h"
#include <math.h>

__global__ void luma_cuda_baseline_kv_int8_kernel(
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
    float local = 0.0f;
    float scale;
    int i;

    if (end > n)
        end = n;

    /* 部分 amax：每个线程扫自己的跨步子集。 */
    for (i = start + tid; i < end; i += nthreads) {
        float a = fabsf(__half2float(x[i]));
        if (a > local)
            local = a;
    }
    smem[tid] = local;
    __syncthreads();

    /* 树归约。nthreads 已保证为 2 的幂。 */
    for (int stride = nthreads >> 1; stride > 0; stride >>= 1) {
        if (tid < stride)
            smem[tid] = fmaxf(smem[tid], smem[tid + stride]);
        __syncthreads();
    }

    if (tid == 0) {
        float amax = smem[0];
        scale = (amax > 0.0f) ? exp2f(floorf(log2f(amax))) : 1.0f;
        scales[block_idx] = scale;
        smem[0] = scale; /* 广播给块内其余线程 */
    }
    __syncthreads();
    scale = smem[0];

    for (i = start + tid; i < end; i += nthreads) {
        float v = __half2float(x[i]) / scale;
        /* 饱和到 int8 可表示的对称区间，避开 -128。 */
        codes[i] = (signed char)rintf(fminf(fmaxf(v, -127.0f), 127.0f));
    }
}

extern "C" int luma_cuda_baseline_kv_int8(
    const __half *x, signed char *codes, float *scales,
    int n, int block_size, int threads_per_block, cudaStream_t stream)
{
    int num_blocks;
    size_t shmem;

    if (!x || !codes || !scales || n <= 0 || block_size <= 0)
        return LUMA_ERR_ARG;
    if (!luma_is_pow2(threads_per_block) || threads_per_block > 1024)
        return LUMA_ERR_ARG;

    num_blocks = (n + block_size - 1) / block_size;
    shmem = sizeof(float) * (size_t)threads_per_block;
    luma_cuda_baseline_kv_int8_kernel<<<num_blocks, threads_per_block, shmem, stream>>>(
        x, codes, scales, n, block_size);
    /* 工程规范：每次 launch 必须查 cudaGetLastError。 */
    if (cudaGetLastError() != cudaSuccess)
        return LUMA_ERR_CUDA;
    return LUMA_OK;
}
