/**
 * @file luma_cuda_util.h
 * @brief CUDA 设备抽象：2 的幂检测 + 块内归约（主机/设备内联）。
 *
 * @note 仅被 .cu include；不进公共 C-ABI。消除各核重复归约代码。
 */
#ifndef LUMA_CUDA_UTIL_H
#define LUMA_CUDA_UTIL_H

#include "baseline/luma_defs.h"

#include <cuda_runtime.h>
#include <math.h>

/**
 * @brief x 是否为 2 的幂且 >0（归约路径要求）。
 * @param[in] x 线程数候选
 * @return 非 0 表示合法
 */
static inline int luma_cuda_is_power_of_two(int x)
{
    return x > 0 && (x & (x - 1)) == 0;
}

/**
 * @brief 块内求和归约（破坏 red[]）。
 * @param[in,out] red 共享内存归约缓冲
 * @param[in] tid 线程号
 * @param[in] nthreads 块内线程数（须为 2 的幂）
 * @return 归约和（各线程可读 red[0] 前需同步）
 */
__device__ static inline float luma_cuda_block_reduce_sum(float *red, int tid, int nthreads)
{
    int stride;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (stride = nthreads >> 1; stride > 0; stride >>= 1) {
        if (tid < stride)
            red[tid] += red[tid + stride];
        /* 块内同步：共享内存读写屏障。 */
        __syncthreads();
    }
    return red[0];
}

/**
 * @brief 块内最大值归约（破坏 red[]）。
 * @param[in,out] red 共享内存归约缓冲
 * @param[in] tid 线程号
 * @param[in] nthreads 块内线程数
 * @return 块内最大
 */
__device__ static inline float luma_cuda_block_reduce_max(float *red, int tid, int nthreads)
{
    int stride;

    /* 有限长度扫描：边界由调用方校验，避免越界读。 */
    for (stride = nthreads >> 1; stride > 0; stride >>= 1) {
        if (tid < stride)
            red[tid] = fmaxf(red[tid], red[tid + stride]);
        /* 块内同步：共享内存读写屏障。 */
        __syncthreads();
    }
    return red[0];
}

/**
 * @brief 启动前公共校验：指针非空 + 2 的幂线程数。
 * @return LUMA_OK | LUMA_ERR_ARG
 */
static inline int luma_cuda_launch_validate(int threads_per_block, int need_ptrs_ok)
{
    if (!need_ptrs_ok)
        return LUMA_ERR_ARG;
    if (!luma_cuda_is_power_of_two(threads_per_block) || threads_per_block > 1024)
        return LUMA_ERR_ARG;
    return LUMA_OK;
}

#endif /* LUMA_CUDA_UTIL_H */
