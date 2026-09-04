# lumina/algorithm — 纯算法层

> 分层裁决：`lumina/docs/arc/LUM-ARC-101`（v1 生效，Phase A/B 已迁移）。本目录存放平台无关的纯算法/参考实现及其自含契约头。

## 当前文件

| 文件 | 职责 |
|---|---|
| `luma_kv.h` | 纯算法层契约头：错误码 + 错误串 + 产品 Enc/Dec + FP64 预言机声明（自含，不依赖 kernel/） |
| `luma_status.c` | 错误码 → 稳态英文短句（随错误码定义归属本层） |
| `luma_kv_ref.c` | 产品路径 FP64 预言机（有限输入恒等复制，供 L1/L5 对照） |
| `luma_kv_codec.c` | 产品路径 Enc/Dec（当前为有限性检查后的恒等映射占位） |
| `CMakeLists.txt` | 独立静态库目标 `luma_algorithm`（被 `kernel/` 依赖） |

## 规则

- 平台无关、纯 ANSI C；无系统 API、无 CUDA、无副作用、无全局状态（`lumina-eng-skill` 最高优先级章节）。
- 头文件仅接口声明；`.h` ≤ 300 行、`.c` ≤ 500 行、函数 ≤ 80 行。
- 本层源只 include 本层契约头 `luma_kv.h`；不得 include `../kernel/` 或 `../wrapper/` 头（Phase B 已消除反向依赖）。
- 构建统一走顶层 `lumina/CMakeLists.txt`（superproject）；本层仅产出 `luma_algorithm`，不直接产可执行/绑定。

## 不应放入

- CUDA/平台算子 → `../kernel/`
- 对外 API / 绑定 / 内存与错误封装 → `../wrapper/`
- 有损基线 → `../kernel/baseline/`
