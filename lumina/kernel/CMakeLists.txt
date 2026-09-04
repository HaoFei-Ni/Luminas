# Luminas 内核：C99 产品核 + 有损基线；CUDA / pybind 可选。
# 不链接 LAPACK。测试目标 luma_test_kv / luma_test_baseline 始终构建。
cmake_minimum_required(VERSION 3.18)
project(lumina_kernels LANGUAGES C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(LUMINA_BUILD_PYTHON "Build pybind11 modules when pybind11 is found" ON)
option(LUMINA_BUILD_CUDA "Build CUDA baseline kernels" OFF)
option(LUMINA_BUILD_FUSED_DECODE "Include fused-decode baseline in the CUDA lib" OFF)

set(LUMA_CPU_SOURCES
    luma_status.c
    luma_kv_ref.c
    luma_kv_cpu.c
    baseline/luma_baseline_ternary.c
    baseline/luma_baseline_mxfp.c
    baseline/luma_baseline_truncated_svd.c
)

add_library(luma_cpu STATIC ${LUMA_CPU_SOURCES})
target_include_directories(luma_cpu PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
if(NOT WIN32)
    target_link_libraries(luma_cpu PUBLIC m)
endif()

add_executable(luma_test_kv test/test_luma_kv.c)
target_link_libraries(luma_test_kv PRIVATE luma_cpu)

add_executable(luma_test_baseline test/test_luma_baseline.c)
target_link_libraries(luma_test_baseline PRIVATE luma_cpu)

enable_testing()
add_test(NAME luma_test_kv COMMAND luma_test_kv)
add_test(NAME luma_test_baseline COMMAND luma_test_baseline)

if(LUMINA_BUILD_PYTHON)
    find_package(pybind11 CONFIG QUIET)
    if(pybind11_FOUND)
        pybind11_add_module(_luma_native luma_bind_native.cpp)
        target_link_libraries(_luma_native PRIVATE luma_cpu)
    else()
        message(STATUS "pybind11 not found; skipping _luma_native")
    endif()
endif()

if(LUMINA_BUILD_CUDA)
    enable_language(CUDA)
    find_package(CUDAToolkit REQUIRED)
    set(LUMA_CUDA_SOURCES baseline/luma_cuda_baseline_kv_int8.cu)
    if(LUMINA_BUILD_FUSED_DECODE)
        list(APPEND LUMA_CUDA_SOURCES baseline/luma_cuda_baseline_fused_decode.cu)
    endif()
    add_library(luma_cuda STATIC ${LUMA_CUDA_SOURCES})
    target_include_directories(luma_cuda PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
    target_link_libraries(luma_cuda PUBLIC CUDA::cudart luma_cpu)
    set_target_properties(luma_cuda PROPERTIES CUDA_ARCHITECTURES "75;80;86;89")

    if(LUMINA_BUILD_PYTHON AND pybind11_FOUND)
        pybind11_add_module(_luma_cuda luma_bind_cuda.cpp)
        target_link_libraries(_luma_cuda PRIVATE luma_cuda)
    endif()
endif()
