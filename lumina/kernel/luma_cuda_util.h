/* luma_cuda_util.h — CUDA 基线共享内部工具。
 *
 * 主机/设备通用的 2 次幂判断 + 块内求和归约。
 * 仅被 .cu 源 include；不在公共 C-ABI 头中暴露。
 */
#ifndef LUMA_CUDA_UTIL_H
#define LUMA_CUDA_UTIL_H

#include <cuda_runtime.h>

/* 主机/设备：x 是否为 2 的幂且 > 0。 */
static inline int luma_is_pow2(int x)
{
    return x > 0 && (x & (x - 1)) == 0;
}

/* 设备：块内求和归约。调用前后由调用方负责 __syncthreads 边界。 */
__device__ static inline float luma_reduce_sum(float *red, int tid, int nthreads)
{
    for (int stride = nthreads >> 1; stride > 0; stride >>= 1) {
        if (tid < stride)
            red[tid] += red[tid + stride];
        __syncthreads();
    }
    return red[0];
}

#endif /* LUMA_CUDA_UTIL_H */
