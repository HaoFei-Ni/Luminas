# Luminas 平台封装层：pybind11 绑定，纯胶水，无数值逻辑。
# 依赖 kernel（luma_cpu / luma_cuda）；仅在 pybind11 可用时构建。
if(NOT LUMINA_BUILD_PYTHON)
    return()
endif()

find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    message(STATUS "pybind11 not found; skipping _luma_native / _luma_cuda")
    return()
endif()

pybind11_add_module(_luma_native luma_bind_native.cpp)
target_link_libraries(_luma_native PRIVATE luma_cpu)

if(LUMINA_BUILD_CUDA)
    pybind11_add_module(_luma_cuda luma_bind_cuda.cpp)
    target_link_libraries(_luma_cuda PRIVATE luma_cuda)
endif()
