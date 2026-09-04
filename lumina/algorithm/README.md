# lumina/algorithm — 纯算法层

> 分层裁决：`lumina/docs/arc/LUM-ARC-101`（v1 生效，Phase A 已迁移）。本目录存放平台无关的纯算法/参考实现。

## 当前文件

| 文件 | 职责 |
|---|---|
| `luma_kv_ref.c` | 产品路径 FP64 预言机（有限输入恒等复制，供 L1/L5 对照） |
| `luma_kv_cpu.c` | 产品路径 Enc/Dec（当前为有限性检查后的恒等映射占位） |

## 规则

- 平台无关、纯 ANSI C；无系统 API、无 CUDA、无副作用、无全局状态（`eng-standard-skill` 最高优先级章节）。
- 头文件仅接口声明；`.h` ≤ 300 行、`.c` ≤ 500 行、函数 ≤ 80 行。
- **已知技术债**：本层源目前 `#include "luma_kernels.h"`（位于 `../kernel/`），经 CMake include 路径解析。分层上本层应自含接口头；拆分见 LUM-ARC-101 Phase B。

## 不应放入

- CUDA/平台算子 → `../kernel/`
- 对外 API / 绑定 / 内存与错误封装 → `../wrapper/`
- 有损基线 → `../kernel/baseline/`
