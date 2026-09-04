# Luminas 纯算法层：平台无关 ANSI C，无 CUDA / 系统 API 依赖。
# 只产出静态库 luma_algorithm（错误串 + FP64 预言机 + 产品 Enc/Dec）。
add_library(luma_algorithm STATIC
    luma_status.c
    luma_kv_finite.c
    luma_kv_ref.c
    luma_kv_encode.c
    luma_kv_decode.c
)
target_include_directories(luma_algorithm PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
