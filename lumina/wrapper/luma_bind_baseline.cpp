/* luma_bind_baseline.cpp — 有损基线 pybind 胶水（quant / SVD）。
 *
 * 允许：dtype/连续性检查、缓冲分配、GIL 释放、错误码→异常。
 * 禁止：产品 luma_kv_* 数学；禁止把本模块表述为无损路径。
 */
#include "luma_kernel.h"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <stdexcept>
#include <string>

namespace py = pybind11;

/* 统一把 luma 错误码映射成 Python 异常，避免裸 int 泄漏到解释器。 */
static void luma_throw(int rc, const char *op)
{
    throw std::runtime_error(std::string(op) + ": " + luma_strerror(rc));
}

/* 绑定层只收 C 连续 float32，防止静默跨步/dtype 错误进核。 */
static void luma_require_c_f32(const py::array &a, const char *name)
{
    if (a.dtype().kind() != 'f' || a.dtype().itemsize() != 4)
        throw std::runtime_error(std::string(name) + " must be float32");
    if ((a.flags() & py::array::c_style) == 0)
        throw std::runtime_error(std::string(name) + " must be C-contiguous");
}

/* SVD 入口限定 2-D float64，与 C-ABI 行主序契约对齐。 */
static void luma_require_c_f64_2d(const py::array &a, const char *name)
{
    if (a.ndim() != 2)
        throw std::runtime_error(std::string(name) + " must be 2-D");
    if (a.dtype().kind() != 'f' || a.dtype().itemsize() != 8)
        throw std::runtime_error(std::string(name) + " must be float64");
    if ((a.flags() & py::array::c_style) == 0)
        throw std::runtime_error(std::string(name) + " must be C-contiguous");
}

/* 有损三值基线绑定：返回 (scale, codes)。 */
static py::tuple quant_ternary_encode(py::array_t<float, py::array::c_style> w, float threshold)
{
    luma_require_c_f32(w, "w");
    auto buf = w.request();
    long n = static_cast<long>(buf.size);
    py::array_t<signed char> codes(n);
    float scale = 0.0f;
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_quant_ternary_encode(static_cast<const float *>(buf.ptr), &scale,
                                       codes.mutable_data(), n, threshold);
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_quant_ternary_encode");
    return py::make_tuple(scale, codes);
}

/* 有损 power-of-two 块量化绑定。 */
static py::array_t<float> quant_power_of_two_encode(py::array_t<float, py::array::c_style> x,
                                                    int mantissa_bits, int block_size)
{
    luma_require_c_f32(x, "x");
    auto buf = x.request();
    long n = static_cast<long>(buf.size);
    py::array_t<float> out(n);
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_quant_power_of_two_encode(static_cast<const float *>(buf.ptr), out.mutable_data(),
                                            n, mantissa_bits, block_size);
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_quant_power_of_two_encode");
    return out;
}

/* 有损截断 SVD 绑定：r 夹紧到合法秩，避免 Python 侧直接崩。 */
static py::tuple svd_truncate(py::array_t<double, py::array::c_style> x, int r)
{
    luma_require_c_f64_2d(x, "x");
    auto buf = x.request();
    int m = static_cast<int>(buf.shape[0]);
    int n = static_cast<int>(buf.shape[1]);
    if (r <= 0)
        throw std::runtime_error("r must be > 0");
    int rank = r;
    if (rank > m)
        rank = m;
    if (rank > n)
        rank = n;
    py::array_t<double> u({m, rank});
    py::array_t<double> s(rank);
    py::array_t<double> vt({rank, n});
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_svd_truncate(static_cast<const double *>(buf.ptr), u.mutable_data(),
                               s.mutable_data(), vt.mutable_data(), m, n, rank);
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_svd_truncate");
    return py::make_tuple(u, s, vt);
}

PYBIND11_MODULE(_luma_baseline, m)
{
    m.doc() = "Luminas lossy baselines only. Never the product lossless KV path.";
    m.def("luma_quant_ternary_encode", &quant_ternary_encode, "lossy ternary weight baseline");
    m.def("luma_quant_power_of_two_encode", &quant_power_of_two_encode,
          "lossy power-of-two block baseline");
    m.def("luma_svd_truncate", &svd_truncate, "lossy truncated SVD baseline");
}
