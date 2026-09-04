# LUM-ENG-101 各语言编码规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 草案 |
| 版本 | 1.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-eng-skill` |
| 关联文档 | `LUM-ENG-001` · `LUM-ARC-101` |
| 依据 | Google C++ Style · PyTorch · 既有 `luma_*` / `LUMA_*` 约定 |

本文件规定命名、符号、目录、文件与文档编号；不与 `lumina-eng-skill` 硬性工程条款冲突，仅做命名侧标准化。

## 0. 项目身份命名（最高优先级）

本项目同时出现四种拼写，必须收敛为一个权威口径：

| 语境 | 规范写法 | 说明 |
|---|---|---|
| 项目名（人读） | `Luminas` | 仓库名、论文标题、README 首行 |
| 目录 / 包名（路径） | `lumina` | 唯一内容区目录；Python 包若发布为 `lumina` |
| C 符号前缀 | `luma_` | 导出函数/结构体/文件局部函数统一 `luma_` 前缀 |
| 宏 / 错误码前缀 | `LUMA_` | 全大写 + 下划线 |
| 文档编号前缀 | `LUM-` | 见 §6 |

禁止再出现 `luminas_*`、`Lumina*`、`LUMINA_*` 等混合拼写。**已存在的 `luma` 符号前缀是既定事实，保留；`lumina` 目录名保留；仅禁止继续新增第四种拼写。**

## 1. C / C++ 命名规范

### 1.1 函数与变量（snake_case）

- 导出符号：`luma_<模块>_<算法?>_<动作>[_<dtype>]`，动作在尾（或紧接 dtype 前）。例：`luma_kv_encode_f32`、`luma_quant_ternary_encode`、`luma_quant_power_of_two_encode`、`luma_svd_truncate`、`luma_cuda_fused_decode`、`luma_cuda_kv_quant_int8`。
- 禁止颠倒动作语序（如 `*_decode_fused` → `*_fused_decode`）；禁止缺动作的名词串（如 `*_block_power_of_two` 无 `encode`）。
- 文件局部（`static`）：一律带模块前缀（即使不导出），如 `luma_svd_jacobi_sym_eig`、`luma_svd_gram_xt_x`、`luma_math_require_finite_f32`。
- 动作词固定：`encode` / `decode` / `quant` / `copy` / `ref` 语义见 §3。
- dtype 后缀固定小写：`f32` / `f64`（禁止 `F32`/`float`/`f32x` 混用）。

### 1.2 类型

- C 结构体：`luma_<name>_t`（typedef 匿名 struct），字段 `snake_case`。
- C++ 类/结构体：`PascalCase`（Google 风格），如 `LumaDeviceBuf`（现有实现正确，保留）。
- 枚举：**命名枚举**，禁止匿名 `enum {}`：`typedef enum luma_status_e { LUMA_OK = 0, ... } luma_status_t;`。

### 1.3 宏与常量

- 宏：`LUMA_<NAME>` 全大写 + 下划线，如 `LUMA_JACOBI_MAX_DIM`。
- 编译期常量优先用 `constexpr`/`enum` 而非宏；数值容差、阈值一律**具名常量**，禁止魔法数字（见 §8）。
- include guard：`LUMA_<FILE>_H`（与文件名对齐）。

### 1.4 参数与局部

- 公共 API 入参 ≤ 5；超出用结构体封装（`luma_*_params_t` / `luma_cuda_fused_decode_args_t`）。
- 长度/索引用固定宽度类型 `int64_t`/`int32_t`，禁止在 CPU/CUDA 两套 ABI 混用 `long` 与 `int` 表同一逻辑量（现 `luma_kv_*` 用 `long`、CUDA 用 `int`，需统一）。

## 2. 平台/角色前缀（与分层对齐）

| 前缀 | 含义 | 落位目录 |
|---|---|---|
| `luma_kv_*` / `luma_kv_ref_*` | 产品无损 KV（预言机 + Enc/Dec） | `algorithm/` |
| `luma_math_*` | Level-1 共享原语 | `kernel/baseline/` |
| `luma_quant_*` / `luma_svd_*` | CPU 有损对照 | `kernel/baseline/` |
| `luma_cuda_*` | CUDA 启动器 / 设备核 | `kernel/cuda/` + `kernel/luma_cuda*.h` |
| `luma_triton_*` | Triton 内核（未启用） | `kernel/` |
| `luma_strerror` / 错误码 | 公共错误语义 | `algorithm/`（随错误码定义，见 LUM-ARC-101 Phase B） |

## 3. 禁用误导性命名

- 禁用 `mxfp`：本实现非 OCP MXFP 规范，旧名 → `luma_quant_power_of_two_encode`。
- 禁用 `cpu` 修饰平台无关算法文件：`luma_kv_cpu.c` → `luma_kv_codec.c`（`algorithm/` 是平台无关层）。
- 禁用文件名重复目录语义：`baseline/` 下禁止再写 `luma_baseline_*` 文件名；用 `luma_quant_*` / `luma_svd_*` / `luma_math_*`。
- 缩写白名单：`kv`、`svd`、`cuda`、`max`、`min`、`dim`、`num`、`pow2→power_of_two`。禁用 `cla`、`mxfp`、`ata/aat`（改 `gram_xt_x` / `gram_x_xt`）。

## 4. Python 命名规范

- 模块/函数/变量：`snake_case`；类 `PascalCase`；常量 `UPPER_SNAKE`（如 `ULP32`）。
- 绑定导出名**必须与 C ABI 符号一一对应**，不得脱落 `luma_`/`cuda_` 前缀：
  - `_luma_native.luma_kv_encode` / `luma_quant_ternary_encode` / `luma_svd_truncate`；
  - `_luma_cuda.luma_cuda_kv_quant_int8`。
- 测试文件：`test_*.py`；核验脚本：`verify_*.py`；二者区分，不得混用。
## 5. 文件 / 目录命名规范

- 文件：`luma_<name>.<ext>`（源码）；`test_<name>.<ext>`（测试）；`LUM-XXX-NNN_<en>.md`（文档）。
- 目录：小写英文 `snake_case`（`algorithm/ kernel/ wrapper/ theory/ research/ experiments/ refs/ docs/`）；归档 `EXP-YYYYMMDD-XXX/`。
- **文件名一律 ASCII**：文档标题含中文时，中文只进正文标题，文件名用英文短横线（`LUM-ARC-001_architecture.md`、`refs/index.md`）。
- 头文件：公共契约头用 `luma_<层>.h`（如 `luma_kernel.h` / `luma_cuda.h` / `luma_kv.h`）；内部头用 `luma_<层>_<角色>.h`；**禁止**废弃泛名 `luma_kernels.h` / `luma_cuda_kernels.h`，以及模糊段 `util` / `defs` / `helper` / `common` / `misc`。

## 6. 文档编号规范（LUM-XXX-NNN）

- `LUM-ARC-*` 架构 / `LUM-ENG-*` 工程 / `LUM-RES-*` 科研 / `LUM-PM-*` 项目。
- 三级：`001` 总纲 → `1xx` 设计 → `2xx` 专项 → `3xx` 接口/体系。
- 单一权威：分层裁决唯一在 `LUM-ARC-101`；理论判据编号唯一在 `theory/state-cache/`（**F1–F7**，表征坍缩框架；权威稿 `framework.tex`），其余推导文档引用同一编号，禁止另立 `§1–§22` 或旧 **P0–P5** 平行体系。
- 产品路径工程分层仍用 **L1–L5**（`lumina-eng-skill/references/test-matrix.md`）；勿把 F 编号与 L 编号混用。

## 7. 测试树命名

- C 测试统一放 `tests/c/`，Python 测试统一放 `tests/python/`（已落地，2026-09）。正式产品 CI 以 `tests/` + ctest 为准。
- 理论核验在 `theory/state-cache/verify/`：主入口 `verify-degeneration.py`（F1–F7）；`check_identity.py` 为旧恒等脚手架，非 F 门。
- 产品 2-ulp / L5 注释引用 **L5**（或历史「重构+2-ulp」语义），阈值用共享常量 `LUMA_ULP32 = 2^-23`，禁止在多处硬编码 `1.1920928955078125e-7`。理论 F2/F6/F7 用各自绝对容差，不套用 2-ulp。

## 8. 注释规范（强制）

原则：**只写 why**（不变量 / 精度阶 / 边界 / 为何不能改），禁止复述 what。

| 层级 | 要求 |
|---|---|
| 文件头 | `@file` + 模块职责、数值契约、非目标（有损/无损） |
| 对外声明 / 定义 | Doxygen：`@brief` `@param` `@return` `@note`（精度与适用场景） |
| **行内注释** | 复杂场景**必须**贴在关键语句旁或紧上一行：稳定公式选型、对称性约定、同步点、除零/溢出防护、与门禁拆循环的原因 |

复杂场景示例（须行内注释）：Jacobi 旋转角、在线 softmax 重标定、power-of-two/尾数 frexp、CUDA `__syncthreads` 前后共享状态、Gram 上三角镜像、σ≈0 置零。

门禁：`quality-gate.toml` `[comment_standard]` 由 `c_quality_gate` / `ci_quality_gate` **强制接线**：
文件 banner、函数/声明前置文档、复杂语句行内注释（循环 / `__syncthreads` / `frexp`/`ldexp`/`exp2f`/`floor(log2)`；Python 为 `for`/`while` + `#`）。
- **L0**（默认存在性）：邻接有注释即过。
- **L4**（`require_why_semantics`）：邻接注释须命中 why 线索词，且不得是 what 模板句；默认 `why_include_file_patterns = ["**"]`（全生产路径最高档）。
- **L2 扩模式**：另检 `__shared__` / `atomic*` 等。

## 8.1 命名门禁（专业最高档，强制）

`quality-gate.toml` `[naming_standard]` → `tools.checks.naming.gate`：

- 文件：`luma_` 前缀；`baseline/` 下禁止文件名再含 `baseline`；禁用误导词与模糊段（`util`/`defs`/`helper`/`tmp`…）；缩写 `pow2` 必须写成 `power_of_two`。
- 符号：`luma_<module>_<action…>`（≥3 段）；禁止双下划线/尾部下划线；层模块对齐；文件-符号模块前缀一致；dtype 仅 `_f32`/`_f64`。
- 宏：公共宏 `LUMA_*`；禁止 `LUMA_BASELINE_*`；头文件 include guard 必须为 `LUMA_<STEM>_H`。
- 层头：`luma_kernel.h` / `luma_cuda.h` / `luma_kv.h` / `luma_limits.h` / `luma_cuda_device.h`。

## 8.2 性能门禁（L4 最高档，强制）

`quality-gate.toml` `[perf_standard]` → `tools.checks.performance.gate`：

- 协议固定：2 warmup + 5 timed；报告 mean±std；禁止 best-of-N / 缩小 warmup。
- 相对校准分数（bench/calib）相对 `tests/python/baselines/l4_perf_baseline.json` 延迟升高 ≤ 2%。
- `max_latency_regression` 不得放宽超过 0.02；缺基线直接失败。

## 9. 无魔法数字（强制）

容差/阈值必须具名（已落地）：`LUMA_TERNARY_NEAR_ZERO`、`LUMA_JACOBI_*`、`LUMA_SVD_SINGULAR_EPS`、`LUMA_ULP32`。禁止 `LUMA_BASELINE_*` 别名与函数体/测试体内散落裸数字。

## 10. 落地顺序（不破坏语义）

1. 先定项目身份口径（§0）并记录，冻结为唯一写法。
2. 头拆分（LUM-ARC-101 Phase B）：抽 `include/luma_kv.h`，消除 algorithm→kernel include。
3. 符号/文件重命名按 §3/§5 批量执行（`git mv` + 全仓替换符号，一次一提交）。
4. 测试树合并（§7），跑 `ctest`/`pytest` 全绿后再进下一步。
