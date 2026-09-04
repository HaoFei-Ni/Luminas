# LUM-ARC-101 核心分层架构设计

- 状态：**v1（已生效，2026-09-04）— 本文件是"四层职责"与"三层物理目录"冲突的唯一裁决点**
- 关联：`LUM-ARC-001` · `luminas-arch-skill` · `eng-standard-skill`（最高优先级章节）

## 背景：两套模型并存

仓库存在两套被不同技能引用的分层模型，本文件负责收敛，禁止任何新代码/新目录绕开本裁决自定归属：

| 视图 | 来源 | 内容 |
|---|---|---|
| 职责视图（4 层） | `luminas-arch-skill`（拥有 source tree） | Kernel → Binding → Scheduler → Infra |
| 物理目录视图（3 层） | `eng-standard-skill` 最高优先级章节 | `algorithm/` → `kernel/` → `wrapper/` |

## 裁决原则（v1 生效）

1. **两者不是同一分类轴**：4 层回答"谁做什么职责"；3 层回答"代码放哪个物理目录"。任何层必须同时满足两个视图：职责看 4 层、落位看 3 层目录。
2. **物理目录语义**：
   - `lumina/algorithm/` — 平台无关 ANSI C 压缩/解压数学（纯逻辑、无系统 API、无 CUDA、无副作用、无全局状态）。
   - `lumina/kernel/` — CUDA / CPU 算子、并行映射、`cuda*` 适配、有损基线、C-ABI 头；算子只调用 algorithm 的纯逻辑，不重实现本体。
   - `lumina/wrapper/` — 对外 C-ABI / pybind11 绑定、内存与错误处理封装、上层稳定接口（Binding 职责落此）。
   - `lumina/theory/`、`lumina/research/` → 方法研究 / 实验协议，非代码层。
3. **Scheduler / Infra 职责**不因 3 层目录而消失：Python 调度仍只做编排，不做算子/KV 数学；Rust infra 若启用单独目录（`lumina/infra/`）。
4. **接口隔离**：层头文件只暴露最小接口，不含实现；未来新头按层自含，禁止跨层 include 非契约头（历史例外见 Phase B 技术债）。

## 层间规则

- 禁止反向依赖与同层循环依赖：`algorithm/` 不得 include `kernel/` 或 `wrapper/` 头；`kernel/`、`wrapper/` 可向下依赖。
- 所有迁移先出迁移单（commit 粒度），禁止一次性大挪移。

## 执行记录

### Phase A（已完成，2026-09-04）

| 迁移 | 内容 |
|---|---|
| `kernel/luma_kv_ref.c`、`kernel/luma_kv_cpu.c` | → `algorithm/`（纯算法/参考实现） |
| `kernel/luma_bind_native.cpp`、`kernel/luma_bind_cuda.cpp` | → `wrapper/`（pybind11 编组） |
| `kernel/CMakeLists.txt` | 源路径改 `../algorithm/`、`../wrapper/`；include 解析经 `target_include_directories(luma_cpu PUBLIC <kernel>)` |

> 验证：MSVC 19.51（BuildTools 18）+ Ninja 可构建。统一入口为 superproject：`cmake -S lumina -B outputs/build/lumina && cmake --build outputs/build/lumina && ctest --test-dir outputs/build/lumina --output-on-failure`。

### Phase B（已完成，2026-09-04）

**原技术债**：`algorithm/` 源 `#include "luma_kernels.h"`（位于 `kernel/`），构成 algorithm→kernel 的头依赖。已按下列方案消除：

1. 抽出纯算法层契约 → `algorithm/luma_kv.h`（错误码、`luma_strerror`、`luma_kv_*` / `luma_kv_ref_*` 声明）。
2. `kernel/luma_kernels.h` 只保留基线/CUDA 声明（`luma_baseline_*`）并 `#include "luma_kv.h"`；`LUMA_CUDA_MAX_HEAD_DIM` 迁入 `luma_cuda_kernels.h`。
3. `luma_status.c` 随错误码定义归属 `algorithm/`（**归属决策：algorithm/，非独立 common/**）；`algorithm/` 源改 include 本层 `luma_kv.h`。
4. 同步 `kernel/CMakeLists.txt`（源路径 `../algorithm/luma_status.c`、include 目录加 `../algorithm`）与各 README。

> 构建验证（2026-09-04）：MSVC 19.51（BuildTools 18）+ Ninja 编译 11/11 零警告，`ctest` 2/2 全绿（`luma_test_kv` / `luma_test_baseline`）。命令见 `kernel/README.md`。

### Phase C（已完成，2026-09-04）— 命名规范化 + superproject

在 LUM-ENG-101 命名约束落地后执行：`luma_kv_cpu.c`→`luma_kv_codec.c`；`mxfp`→`pow2_block`；Python 绑定导出名补 `luma_`/`luma_cuda_` 前缀；抽 `kernel/luma_cuda_util.h` 共享 `luma_is_pow2`/`luma_reduce_sum`；容差/阈值具名化；测试树合并为 `tests/c/` + `tests/python/`。

同时建立顶层 superproject `lumina/CMakeLists.txt`，将构建图拆为三层目标：`luma_algorithm`（algorithm/）→ `luma_cpu`/`luma_cuda`（kernel/）→ `_luma_native`/`_luma_cuda`（wrapper/）。`kernel/` 不再跨目录引用 `../algorithm/`、`../wrapper/` 源。

> 验证（2026-09-04）：superproject 编译 12/12，`ctest` 2/2 全绿。

## 待办

- [x] 冻结 `algorithm/`、`wrapper/` 首批文件清单（Phase A）
- [x] 迁移并同步 CMake / README（Phase A）
- [x] Phase B 头拆分（`luma_kv.h` / `luma_status.c` 归 `algorithm/`；ctest 验证待可构建环境）
- [ ] 三技能 owner 终审本 v1（arch / eng / research 已隐含认可，正式签字记录留痕）
