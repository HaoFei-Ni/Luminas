# Luminas superproject：统一构建 algorithm / kernel / wrapper 三层。
# 用法：cmake -S lumina -B outputs/build/lumina && cmake --build outputs/build/lumina
cmake_minimum_required(VERSION 3.18)
project(lumina LANGUAGES C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(LUMINA_BUILD_PYTHON "Build pybind11 modules when pybind11 is found" ON)
option(LUMINA_BUILD_CUDA "Build CUDA baseline kernels" OFF)
option(LUMINA_BUILD_FUSED_DECODE "Include fused-decode baseline in the CUDA lib" OFF)

enable_testing()

add_subdirectory(algorithm)
add_subdirectory(kernel)
add_subdirectory(wrapper)
