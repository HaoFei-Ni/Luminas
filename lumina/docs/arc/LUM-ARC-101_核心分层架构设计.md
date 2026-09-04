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

> 验证：本机无工具链，未跑 `ctest`。构建验证命令：`cmake -S lumina/kernel -B outputs/build/kernel && cmake --build outputs/build/kernel && ctest --test-dir outputs/build/kernel --output-on-failure`。

### Phase B（待办，需构建验证环境）

**技术债**：`algorithm/` 源目前 `#include "luma_kernels.h"`（位于 `kernel/`），构成 algorithm→kernel 的头依赖。拆分方案：

1. 从 `luma_kernels.h` 抽出纯算法层契约 → `algorithm/luma_kv.h`（错误码、`luma_kv_*` / `luma_kv_ref_*` 声明）。
2. `kernel/` 保留基线/CUDA 声明（`luma_baseline_*`、`luma_cuda_*`），include `luma_kv.h`。
3. `wrapper/` 绑定 include 上述头；`luma_status.c` 随错误码定义归属 `algorithm/`（或独立公共位置，二选一并记录）。
4. 同步 `CMakeLists.txt` include 目录与各 README；跑 ctest 全绿后合入。

## 待办

- [x] 冻结 `algorithm/`、`wrapper/` 首批文件清单（Phase A）
- [x] 迁移并同步 CMake / README（Phase A）
- [ ] 三技能 owner 终审本 v1（arch / eng / research 已隐含认可，正式签字记录留痕）
- [ ] Phase B 头拆分（需可构建环境，含 ctest 验证）
