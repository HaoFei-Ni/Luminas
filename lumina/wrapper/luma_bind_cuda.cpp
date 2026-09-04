/* luma_bind_cuda.cpp — CUDA 基线的主机侧编组。
 *
 * 将 host float32 转为设备 fp16 再调 C-ABI。dtype 转换视为编组，不是算法核。
 * 整缓冲 H2D/D2H 只方便测试；生产路径应持有设备指针，避免往返吃掉加速。
 * 每个 cudaMalloc / Memcpy / launch 失败都必须变成异常，禁止吞错。
 */
#include "luma_cuda_kernels.h"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <cuda_fp16.h>
#include <cuda_runtime.h>

#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

static void luma_cuda_or_throw(cudaError_t e, const char *what)
{
    if (e != cudaSuccess)
        throw std::runtime_error(std::string(what) + ": " + cudaGetErrorString(e));
}

/* RAII：任一分配失败时释放已分配的设备缓冲。 */
class LumaDeviceBuf
{
public:
    LumaDeviceBuf() : p_(nullptr) {}
    ~LumaDeviceBuf()
    {
        if (p_)
            cudaFree(p_);
    }
    LumaDeviceBuf(const LumaDeviceBuf &) = delete;
    LumaDeviceBuf &operator=(const LumaDeviceBuf &) = delete;

    void alloc(size_t bytes, const char *what)
    {
        luma_cuda_or_throw(cudaMalloc(&p_, bytes), what);
    }
    void *get() const { return p_; }

private:
    void *p_;
};

static py::tuple baseline_kv_int8(py::array_t<float, py::array::c_style> x, int block_size,
                                  int threads_per_block)
{
    auto buf = x.request();
    if (x.dtype().kind() != 'f' || x.dtype().itemsize() != 4)
        throw std::runtime_error("x must be float32");
    if ((x.flags() & py::array::c_style) == 0)
        throw std::runtime_error("x must be C-contiguous");
    if (block_size <= 0)
        throw std::runtime_error("block_size must be > 0");

    /* C-ABI 用 int 长度；超长输入直接拒绝，避免静默截断。 */
    if (buf.size <= 0)
        throw std::runtime_error("x must be non-empty");
    if (buf.size > static_cast<py::ssize_t>(std::numeric_limits<int>::max()))
        throw std::runtime_error("x too large for int32 kernel ABI");
    int n = static_cast<int>(buf.size);

    int num_blocks = (n + block_size - 1) / block_size;
    py::array_t<float> scales(num_blocks);
    py::array_t<signed char> codes(n);

    const float *h_in = static_cast<const float *>(buf.ptr);
    std::vector<__half> h_half(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i)
        h_half[static_cast<size_t>(i)] = __float2half(h_in[i]);

    LumaDeviceBuf d_in, d_codes, d_scales;
    d_in.alloc(sizeof(__half) * static_cast<size_t>(n), "cudaMalloc in");
    d_codes.alloc(sizeof(signed char) * static_cast<size_t>(n), "cudaMalloc codes");
    d_scales.alloc(sizeof(float) * static_cast<size_t>(num_blocks), "cudaMalloc scales");

    luma_cuda_or_throw(cudaMemcpy(d_in.get(), h_half.data(),
                                  sizeof(__half) * static_cast<size_t>(n),
                                  cudaMemcpyHostToDevice),
                       "H2D");
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_cuda_baseline_kv_int8(static_cast<const __half *>(d_in.get()),
                                        static_cast<signed char *>(d_codes.get()),
                                        static_cast<float *>(d_scales.get()),
                                        n, block_size, threads_per_block, 0);
        /* 默认流：同步后再 D2H，避免未完成拷贝。 */
        if (rc == LUMA_OK && cudaDeviceSynchronize() != cudaSuccess)
            rc = LUMA_ERR_CUDA;
    }
    if (rc == LUMA_OK) {
        luma_cuda_or_throw(cudaMemcpy(codes.mutable_data(), d_codes.get(),
                                      sizeof(signed char) * static_cast<size_t>(n),
                                      cudaMemcpyDeviceToHost),
                           "D2H codes");
        luma_cuda_or_throw(cudaMemcpy(scales.mutable_data(), d_scales.get(),
                                      sizeof(float) * static_cast<size_t>(num_blocks),
                                      cudaMemcpyDeviceToHost),
                           "D2H scales");
    }
    if (rc != LUMA_OK)
        throw std::runtime_error(std::string("luma_cuda_baseline_kv_int8: ") + luma_strerror(rc));
    return py::make_tuple(scales, codes);
}

PYBIND11_MODULE(_luma_cuda, m)
{
    m.doc() = "Luminas CUDA baselines (lossy). Not the product lossless KV path.";
    m.def(
        "luma_cuda_baseline_kv_int8",
        &baseline_kv_int8,
        py::arg("x"),
        py::arg("block_size"),
        py::arg("threads_per_block") = 256,
        "lossy per-block int8 KV baseline");
}
