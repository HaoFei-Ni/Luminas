# lumina/wrapper — 平台封装层

> 分层裁决：`lumina/docs/arc/LUM-ARC-101`（v1 生效，Phase A/B 已迁移）。本目录存放对外 API / 绑定 / 封装。

## 当前文件

| 文件 | 职责 |
|---|---|
| `luma_bind_native.cpp` | pybind11 编组（CPU 产品路径） |
| `luma_bind_cuda.cpp` | pybind11 编组（CUDA 基线，host↔device） |
| `CMakeLists.txt` | pybind11 模块 `_luma_native` / `_luma_cuda`（依赖 kernel 目标） |

## 规则

- 只做 marshal、dtype/shape 校验、GIL 释放、错误码→异常；**无数值算法**。
- 编译时经 `target_link_libraries(... luma_cpu / luma_cuda)` 传递 C-ABI 头 include 路径：`luma_kernels.h`（→ include `../algorithm/luma_kv.h`）/ `luma_cuda_kernels.h`。
- 头文件只暴露最小接口；`luma_*` 错误码经 `luma_strerror` 映射为 Python 异常。

## 不应放入

- 数值算法本体 → `../algorithm/` 或 `../kernel/`
- Python 调度/编排 → `../research/` 或调度模块
