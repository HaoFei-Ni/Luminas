/* luma_bind_native.cpp — 产品路径 pybind 胶水（仅 luma_kv_*）。
 *
 * 工程 L5：只 marshal / 校验 / 异常映射；数值契约在 algorithm（2-ulp / bit-exact）。
 * 允许：dtype/连续性检查、缓冲分配、GIL 释放、错误码→异常。
 * 禁止：量化、SVD、CUDA、任何有损基线。有损基线见 _luma_baseline。
 */
#include "luma_kv.h"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <cstring>
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

/* 截断码流拷贝：避免返回临时缓冲内部指针。 */
static py::array_t<float> luma_copy_enc(const float *data, long enc_len)
{
    py::array_t<float> out(enc_len);
    if (enc_len > 0)
        std::memcpy(out.mutable_data(), data, sizeof(float) * static_cast<size_t>(enc_len));
    return out;
}

/* 产品 Enc：按最坏 RLE 分配 2n；返回长度为 enc_len 的拷贝。 */
static py::array_t<float> kv_encode(py::array_t<float, py::array::c_style> x)
{
    luma_require_c_f32(x, "x");
    auto buf = x.request();
    long n = static_cast<long>(buf.size);
    long cap = (n <= 0) ? 0 : n * 2;
    py::array_t<float> enc(cap);
    long enc_len = 0;
    int rc;
    {
        py::gil_scoped_release release;
        rc = luma_kv_encode_f32(static_cast<const float *>(buf.ptr), n,
                                enc.mutable_data(), cap, &enc_len);
    }
    if (rc != LUMA_OK)
        luma_throw(rc, "luma_kv_encode_f32");
    if (enc_len < 0 || enc_len > cap)
        throw std::runtime_error("luma_kv_encode_f32: invalid enc_len");
    return luma_copy_enc(enc.data(), enc_len);
}

/* 产品 Dec：enc_len 与目标 n 由 C-ABI 校验。 */
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

PYBIND11_MODULE(_luma_native, m)
{
    m.doc() = "Luminas product path: bit-exact f32 RLE KV (paper L1 numeric).";
    m.def("luma_kv_encode", &kv_encode,
          "product Enc — exact f32 RLE (bit-exact reconstruction)");
    m.def("luma_kv_decode", &kv_decode, py::arg("enc"), py::arg("n"),
          "product Dec — exact f32 RLE expand");
}
