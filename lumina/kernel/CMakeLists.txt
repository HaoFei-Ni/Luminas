# Luminas 算子适配层：有损基线 + CUDA launchers。
# 依赖 algorithm 契约头（luma_kv.h）；CUDA / fused-decode 可选。
set(LUMA_CPU_SOURCES
    baseline/luma_baseline_ternary.c
    baseline/luma_baseline_pow2_block_quant.c
    baseline/luma_baseline_truncated_svd.c
)

add_library(luma_cpu STATIC ${LUMA_CPU_SOURCES})
target_include_directories(luma_cpu PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(luma_cpu PUBLIC luma_algorithm)
if(NOT WIN32)
    target_link_libraries(luma_cpu PUBLIC m)
endif()

# 测试目标始终构建；C 测试源位于 ../tests/c/。
add_executable(luma_test_kv ../tests/c/test_luma_kv.c)
target_link_libraries(luma_test_kv PRIVATE luma_cpu)

add_executable(luma_test_baseline ../tests/c/test_luma_baseline.c)
target_link_libraries(luma_test_baseline PRIVATE luma_cpu)

add_test(NAME luma_test_kv COMMAND luma_test_kv)
add_test(NAME luma_test_baseline COMMAND luma_test_baseline)

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
endif()
