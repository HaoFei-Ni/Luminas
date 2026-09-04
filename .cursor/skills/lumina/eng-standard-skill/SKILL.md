---
name: eng-standard-skill
description: >-
  Enforces Luminas coding, build, and CI test standards for C99, CUDA, Triton,
  Rust, Python, and pybind11, including luma_ prefixes, numerical 2-ulp checks,
  and discrete GPU memory tiers (8/24/80 GB). Use when writing or reviewing
  kernels, bindings, CMake, tests, or benchmarks, or when the user mentions
  CUDA, Triton, kernel, 算子, nsys, ncu, coverage, pybind11, or luma_ prefixes.
  Do not use for paper structure, ablation design, architecture identity, or
  claiming lossless from unit tests alone.
paths:
  - "lumina/**"
  - "**/*.{c,h,cu,cuh}"
metadata:
  version: "3.0.0"
  owner: luminas
  layer: engineering
---

## 架构级代码强制标准（最高优先级）

> 本章节为项目最高优先级工程规范，优先级高于所有外部技能与通用代码规则。

### 1. 三层正交分层架构

严格执行三层无交叉分层，层间禁止跨层访问与反向依赖，同层禁止循环依赖。

- **第一层：纯算法层（algorithm/）**
  - 平台无关，纯 ANSI C 实现，无任何系统 API 与 CUDA 依赖
  - 只包含核心压缩/解压算法逻辑，无副作用、无全局状态
  - 所有逻辑编译期展开，运行时零循环、零递归
- **第二层：算子适配层（kernel/）**
  - CUDA / CPU 平台专属算子实现，只做硬件适配与并行映射
  - 调用算法层的纯逻辑，不重复实现算法本体
  - 负责显存管理、线程映射、硬件指令适配
- **第三层：平台封装层（wrapper/）**
  - 对外暴露统一 API，封装平台差异、内存管理、错误处理
  - 向上层应用提供稳定接口，内部实现对调用方完全透明
- 接口隔离原则：每层头文件仅暴露最小必要接口，内部实现全部封装在实现文件中，头文件不包含任何实现逻辑。

### 2. 零循环零递归强制规范

- 运行时禁止所有 for / while / do-while 循环指令与递归调用
- 所有线性遍历逻辑必须替换为：编译期展开、查找表(LUT)、位运算批量处理、分支展开、SIMD向量化、全量内联
- 循环仅允许存在于编译期宏展开与模板元编程，运行时执行路径无循环跳转指令
- 所有递归逻辑全部转换为预查表、迭代展开或编译期常量计算

### 3. 结构度量强制标准

- **文件级**
  - 头文件(.h)：单文件 ≤ 300 行，仅包含接口声明、宏定义、结构体声明，不放任何实现代码
  - 实现文件(.c/.cu)：单文件 ≤ 500 行，超出必须按职责拆分为多个独立文件
  - 单个文件内函数数量 ≤ 15 个，超出必须拆分文件
  - 每个文件只对应一个模块，一个模块只负责一类功能
- **函数级**
  - 工具函数：单函数 ≤ 50 行，严格单一职责
  - 核心算法/算子函数：单函数 ≤ 80 行，超出必须拆分为原子子函数
  - 函数入参 ≤ 5 个，超过必须用结构体封装传递
- **复杂度**
  - 单函数圈复杂度 ≤ 5
  - if 分支嵌套 ≤ 2 层，禁止深层分支嵌套
  - 禁止多条件叠加重叠分支

### 4. 极致性能优化规范

- **内存与访存**
  - 所有内存 128 字节对齐，显存访问满足合并访问要求，无 bank 冲突
  - 减少全局内存访问，优先使用寄存器、共享内存
  - 所有偏移量预计算，运行时无动态地址计算
- **指令与分支**
  - 优先使用原生硬件指令，减少指令周期
  - 所有可预计算量全部编译期完成，运行时不做重复计算
  - 最大限度消除条件跳转，用位运算、查表、谓词指令替代分支逻辑
- **内联与调用**
  - 所有小函数强制内联，核心执行路径无函数调用开销
  - 核心路径禁止间接调用、虚函数调用

### 5. 正确性与工程规范

- 无损算法必须保证字节级一致，覆盖所有边界场景：空输入、极值长度、非对齐内存、异常字符
- 所有指针操作做边界校验，无野指针、数组越界、内存泄漏、重复释放
- CUDA 设备内存申请后必须校验返回值，核函数启动后必须检查启动错误
- 命名统一见名知意，无魔法数字，所有常量具名化定义
- 核心优化点必须注释原理，说明无循环等价实现的正确性依据
- 所有错误码清晰可追溯，不静默失败，出错时资源可正确回滚释放

### 6. 架构执行原则

- 单一职责：每个模块、每个函数仅负责一个原子功能，无职责重叠
- 低耦合高内聚：模块间依赖最小化，禁止全局变量跨模块传递状态
- 所有状态通过参数或结构体显式传递，禁止隐式共享状态
- 编译期最大化：一切可在编译期确定的逻辑，全部下沉到编译期完成

# Luminas Engineering Standard

This skill owns code, build, and **CI-grade** tests. It does not redefine "lossless" and does not own paper experiments.

## Priority

1. `luminas-arch-skill` — identity and non-goals (do not implement GPTQ/AWQ/pruning; do not patch upstream)
2. `eng-standard-skill` — this file
3. `research-skill` — PPL / task / statistics / paper
4. Orchestra — baselines and tools only

Test tables and commands: [references/test-matrix.md](references/test-matrix.md).

## When to use

Writing or reviewing anything under `lumina/` in C, CUDA, Triton, Rust, pybind11, or Python bindings/tests.

## Do not use

- Architecture lock, directory isolation → `luminas-arch-skill`
- Ablations, p-values, venue structure → `research-skill`
- Upstream `spb2/` / `MoBA/` style matching

## Coding rules

### C99 CPU reference kernels

Applies to CPU reference and any portable scalar kernel, **not** to `.cu`.

1. C99 only. No C++, no GNU/MSVC extensions in these files.
2. Exported symbols `luma_*`; file-local `static`; macros `LUMA_*`.
3. Explicit allocation; NULL and bounds checks; no implicit grow.
4. Public APIs return `int` error codes. Do not report errors via `errno`.
5. IEEE 754 for the floating-point path you document in the header.

### CUDA C++ kernels

CUDA language extensions are allowed in `.cu` / `.cuh`.

1. Exported kernels / launchers `luma_cuda_*`. Grid and block are parameters, never literals for problem size.
2. Shared memory: no bank conflicts on the hot path; global loads vectorized / coalesced; prefer async copy where the arch supports it.
3. Check every runtime API and `cudaGetLastError()` after launch. Swallowing errors is a defect.
4. Numeric output matches the C99 reference under the L1/L5 gate in [references/test-matrix.md](references/test-matrix.md).
5. Tiling must run on GPU tiers **S=8 GB, M=24 GB, L=80 GB**. Do not claim a continuous 4–120 GB sweep.

### Triton

1. Exported ops `luma_triton_*`. Tile sizes are parameters; keep an autotune table.
2. No implicit cast or silent broadcast. Layout is explicit.
3. If a CUDA twin exists: same shape, same GPU, 2 warmup + 5 timed runs, Triton mean latency ≤ 1.11× CUDA mean (≈ 90% throughput). If no CUDA twin yet, report vs roofline only.

### Rust infra (optional layer)

1. Every `unsafe` block has a safety comment. No `unwrap`/`expect` on library paths.
2. `Result` + `Send`/`Sync` as required. No hidden global device state.

### Python scheduler

1. Glue, module wiring, train/infer entry, tests, **loop control** (Ouro-style). 
2. **No operator math and no KV encode/decode math** in Python. That belongs in `luma_*` / `luma_cuda_*` / `luma_triton_*`.
3. Public functions are fully annotated; `mypy` clean; no process-wide mutable cache.

### pybind11

1. Marshal, validate, translate errors. No numeric algorithm in the binding `.cpp`.
2. Check numpy dtype, rank, and c-contiguity; reject the rest with a clear error.
3. Release the GIL around kernel launches. Map `luma_*` codes to typed Python exceptions.

## Build

1. CMake: kernel / bind / tools as separate targets. One script or `cmake --build` target builds the tested pipeline.
2. Lock compiler, CUDA toolkit, driver family, and Python deps (`uv.lock`). Record versions in every benchmark report.
3. Conventional Commits; one concern per commit. Kernel behavior changes ship with an L1 test.

## Memory tiers

| Tier | VRAM | Default duty |
|---|---|---|
| S | 8 GB | Functional + degrade path |
| M | 24 GB | Default research GPU |
| L | 80 GB | 128k / large batch |

Implement a tile/pool path that **degrades** on OOM (smaller tiles, not silent abort). Degrade must still pass L5 if the kernel is on the lossless KV path. Use `compute-sanitizer` for device leaks; do not rely on `cuda-memcheck`.

## Tests (summary)

All `lumina/` modules: L1 unit, L2 boundary, L3 integration, L4 benchmark. Lossless KV paths also L5. Full gates and coverage: [references/test-matrix.md](references/test-matrix.md).

CI tools: pytest + xdist + Hypothesis; mypy + ruff; nsys / ncu / torch.profiler; compute-sanitizer; pytest-benchmark. Do not block a PR on MLPerf.

Engineering tests **do not** grant a "lossless" paper claim. That claim requires `research-skill`.

## Merge bar

- Static checks + L1–L3 green on the changed module.
- L4 if the change is on a hot kernel (throughput drop ≤ 2% vs last tagged baseline on the same tier).
- L5 if the change touches compress / decompress / residual.
- Release of a core algorithm additionally needs the research reports named in `research-skill`, bound to a commit hash.
