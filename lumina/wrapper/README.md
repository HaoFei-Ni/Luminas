# lumina/wrapper — 平台封装层

> 分层裁决：`lumina/docs/arc/LUM-ARC-101`。接口合同：`LUM-ARC-301`。

## 当前文件

| 文件 | 职责 | 扩展名 |
|---|---|---|
| `luma_bind_native.cpp` | 产品 `luma_kv_*` 编组 | `_luma_native` → `luma_algorithm` |
| `luma_bind_baseline.cpp` | 有损 quant / SVD 编组 | `_luma_baseline` → `luma_cpu` |
| `luma_bind_cuda.cpp` | CUDA 有损基线编组 | `_luma_cuda` → `luma_cuda` |
| `CMakeLists.txt` | 上述 pybind11 模块 | |

## 规则

- 只做 marshal、dtype/shape 校验、GIL 释放、错误码→异常；**无数值算法**。
- **产品与基线分模块导出**，禁止在 `_luma_native` 上挂 quant/SVD。
- 产品头：`luma_kv.h`；基线头：`luma_kernel.h` / `luma_cuda.h`。
- 现行产品 Enc/Dec 为 **candidate** 恒等占位；不得据此报告压缩比或宣称无损。

## 不应放入

- 数值算法本体 → `../algorithm/` 或 `../kernel/`
- Python 调度/编排 → 未来 `../runtime/`（须先改 `LUM-ARC-101`）
