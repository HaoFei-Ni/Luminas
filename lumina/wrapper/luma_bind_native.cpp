/* luma_bind_native.cpp — pybind11 纯胶水。
 *
 * 允许：dtype/连续性检查、缓冲分配、GIL 释放、错误码→异常。
 * 禁止：量化、SVD、KV 数学。数值一律走 luma_kernels.h。
 */
#include "luma_kernels.h"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <stdexcept>
#include <string>

namespace py = pybind11;

static void luma_throw(int rc, const char *op)
{
    throw std::runtime_error(std::string(op) + ": " + luma_strerror(rc));
}

static void luma_require_c_f32(const py::array &a, const char *name)
{
    if (a.dtype().kind() != 'f' || a.dtype().itemsize() != 4)
        throw std::runtime_error(std::string(name) + " must be float32");
    if ((a.flags() & py::array::c_style) == 0)
        throw std::runtime_error(std::string(name) + " must be C-contiguous");
}

static void luma_require_c_f64_2d(const py::array &a, const char *name)
{
    if (a.ndim() != 2)
        throw std::runtime_error(std::string(name) + " must be 2-D");
    if (a.dtype().kind() != 'f' || a.dtype().itemsize() != 8)
        throw std::runtime_error(std::string(name) + " must be float64");
    if ((a.flags() & py::array::c_style) == 0)
        throw std::runtime_error(std::string(name) + " must be C-contiguous");
}

static py::array_t<float> kv_encode(py::array_t<float, py::array::c_style> x)
{
    luma_require_c_f32(x, "x");
    auto buf = x.request();
    long n = static_cast<long>(buf.size);
    py::array_t<float> enc(n);
    long enc_len = 0;
    int rc;
    {
        py::gil_scoped_release release; /* 核函数持锁无益，长序列必须放 GIL。 */
        rc = luma_kv_encode_f32(static_cast<const float *>(buf.ptr), n,
                                enc.mutable_data(), n, &enc_len);
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_kv_encode_f32");
    /* 恒等实现 enc_len==n。真压缩器返回更短表示时，应只暴露前 enc_len 个。 */
    if (enc_len != n)
        throw std::runtime_error("luma_kv_encode_f32: unexpected enc_len");
    return enc;
}

static py::array_t<float> kv_decode(py::array_t<float, py::array::c_style> enc, long n)
{
    luma_require_c_f32(enc, "enc");
    auto buf = enc.request();
    long enc_len = static_cast<long>(buf.size);
    py::array_t<float> out(n);
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_kv_decode_f32(static_cast<const float *>(buf.ptr), enc_len,
                                out.mutable_data(), n);
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_kv_decode_f32");
    return out;
}

static py::tuple baseline_ternary_encode(py::array_t<float, py::array::c_style> w, float threshold)
{
    luma_require_c_f32(w, "w");
    auto buf = w.request();
    long n = static_cast<long>(buf.size);
    py::array_t<signed char> codes(n);
    float scale = 0.0f;
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_baseline_ternary_encode(static_cast<const float *>(buf.ptr), n, threshold,
                                          &scale, codes.mutable_data());
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_baseline_ternary_encode");
    return py::make_tuple(scale, codes);
}

static py::array_t<float> baseline_pow2_block_quant(py::array_t<float, py::array::c_style> x,
                                             int mantissa_bits, int block_size)
{
    luma_require_c_f32(x, "x");
    auto buf = x.request();
    long n = static_cast<long>(buf.size);
    py::array_t<float> out(n);
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_baseline_pow2_block_quant(static_cast<const float *>(buf.ptr), n, mantissa_bits,
                                      block_size, out.mutable_data());
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_baseline_pow2_block_quant");
    return out;
}

static py::tuple baseline_truncated_svd(py::array_t<double, py::array::c_style> x, int r)
{
    luma_require_c_f64_2d(x, "x");
    auto buf = x.request();
    int m = static_cast<int>(buf.shape[0]);
    int n = static_cast<int>(buf.shape[1]);
    if (r <= 0)
        throw std::runtime_error("r must be > 0");
    /* 静默夹紧到 max 合法秩，避免 Python 侧因 r>min(m,n) 直接崩。 */
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
        rc = luma_baseline_truncated_svd(static_cast<const double *>(buf.ptr), m, n, rank,
                                         u.mutable_data(), s.mutable_data(), vt.mutable_data());
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_baseline_truncated_svd");
    return py::make_tuple(u, s, vt);
}

PYBIND11_MODULE(_luma_native, m)
{
    m.doc() = "Luminas native kernels: product luma_kv_* and lossy baselines";
    m.def("luma_kv_encode", &kv_encode, "product Enc (identity placeholder; no compression ratio)");
    m.def("luma_kv_decode", &kv_decode, py::arg("enc"), py::arg("n"),
          "product Dec (identity placeholder)");
    m.def("luma_baseline_ternary_encode", &baseline_ternary_encode, "lossy ternary weight baseline");
    m.def("luma_baseline_pow2_block_quant", &baseline_pow2_block_quant, "lossy power-of-two block baseline");
    m.def("luma_baseline_truncated_svd", &baseline_truncated_svd, "lossy truncated SVD baseline");
}
