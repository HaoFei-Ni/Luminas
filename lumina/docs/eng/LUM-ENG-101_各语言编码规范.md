# LUM-ENG-101 各语言编码规范

- 状态：**草案（待评审，2026-09-04）** — 由全量命名审计产出，作为命名/符号/目录/文件/文档编号的统一约束
- 关联：`LUM-ENG-001` · `eng-standard-skill`（最高优先级章节，本文件不与之冲突，只做命名侧标准化）· `LUM-ARC-101`（分层裁决）
- 依据：Google C++ Style Guide · PyTorch(Meta) · OpenAI · Microsoft 开源命名规约，收敛到本项目既有 `luma_*` / `LUMA_*` 约定

## 0. 项目身份命名（最高优先级，先于一切符号规则）

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

- 导出符号：`luma_<模块>_<动作>[_<dtype>]`，如 `luma_kv_encode_f32`、`luma_baseline_ternary_encode`、`luma_cuda_baseline_kv_int8`。
- 文件局部（`static`）：一律 `luma_` 前缀（即使不导出），如 `luma_jacobi_sym_eig`、`luma_gram_ata`、`luma_is_power_of_two`。
- 动作词固定：`encode` / `decode` / `quant` / `copy` / `ref` 语义见 §3。
- dtype 后缀固定小写：`f32` / `f64`（禁止 `F32`/`float`/`f32x` 混用）。

### 1.2 类型

- C 结构体：`luma_<name>_t`（typedef 匿名 struct），字段 `snake_case`。
- C++ 类/结构体：`PascalCase`（Google 风格），如 `LumaDeviceBuf`（现有实现正确，保留）。
- 枚举：**命名枚举**，禁止匿名 `enum {}`：`typedef enum luma_status_e { LUMA_OK = 0, ... } luma_status_t;`。

### 1.3 宏与常量

- 宏：`LUMA_<NAME>` 全大写 + 下划线，如 `LUMA_BASELINE_JACOBI_MAX_DIM`。
- 编译期常量优先用 `constexpr`/`enum` 而非宏；数值容差、阈值一律**具名常量**，禁止魔法数字（见 §8）。
- include guard：`LUMA_<FILE>_H`（与文件名对齐）。

### 1.4 参数与局部

- 公共 API 入参 ≤ 5；超出用结构体封装（`luma_*_params_t`）。
- 长度/索引用固定宽度类型 `int64_t`/`int32_t`，禁止在 CPU/CUDA 两套 ABI 混用 `long` 与 `int` 表同一逻辑量（现 `luma_kv_*` 用 `long`、CUDA 用 `int`，需统一）。

## 2. 平台/角色前缀（与分层对齐）

| 前缀 | 含义 | 落位目录 |
|---|---|---|
| `luma_kv_*` / `luma_kv_ref_*` | 产品无损 KV（预言机 + Enc/Dec） | `algorithm/` |
| `luma_baseline_*` | CPU 有损对照 | `kernel/baseline/` |
| `luma_cuda_*` | CUDA 启动器（工程前缀） | `kernel/` |
| `luma_cuda_baseline_*` | GPU 有损对照 | `kernel/baseline/` |
| `luma_triton_*` | Triton 内核（未启用） | `kernel/` |
| `luma_strerror` / 错误码 | 公共错误语义 | `algorithm/`（随错误码定义，见 LUM-ARC-101 Phase B） |

## 3. 禁用误导性命名

- 禁用 `mxfp`：本实现非 OCP MXFP 规范，`luma_baseline_mxfp_quant` → `luma_baseline_pow2_block_quant`。
- 禁用 `cpu` 修饰平台无关算法文件：`luma_kv_cpu.c` → `luma_kv_codec.c`（`algorithm/` 是平台无关层）。
- 禁用 "baseline" 多义：代码里 `baseline` 仅指"有损对照核"；文档里"基准压缩比"改称 `reference_rate` / `nominal_case`，与代码语义解耦。
- 缩写白名单：`kv`、`svd`、`cuda`、`max`、`min`、`dim`、`num`、`pow2→power_of_two`。禁用 `cla`（语义不明）、`mxfp`、`ata/aat`（改 `gram_ata`→`gram_xt_x`、`gram_aat`→`gram_x_xt`）。

## 4. Python 命名规范

- 模块/函数/变量：`snake_case`；类 `PascalCase`；常量 `UPPER_SNAKE`（如 `ULP32`）。
- 绑定导出名**必须与 C ABI 符号一一对应**，不得脱落 `luma_`/`cuda_` 前缀：
  - 现 `_luma_native.kv_encode` → `luma_kv_encode`；`baseline_ternary_encode` → `luma_baseline_ternary_encode`；
  - `_luma_cuda.baseline_kv_int8` → `luma_cuda_baseline_kv_int8`。
- 测试文件：`test_*.py`；核验脚本：`verify_*.py`；二者区分，不得混用（现 `verify-kv-compression-baseline.py` 用连字符且无 `test_` 前缀，需统一为 `verify_rate_formula.py` 或 `test_rate_formula.py`）。

## 5. 文件 / 目录命名规范

- 文件：`luma_<name>.<ext>`（源码）；`test_<name>.<ext>`（测试）；`LUM-XXX-NNN_<en>.md`（文档）。
- 目录：小写英文 `snake_case`（`algorithm/ kernel/ wrapper/ theory/ research/ experiments/ refs/ docs/`）；归档 `EXP-YYYYMMDD-XXX/`。
- **文件名一律 ASCII**：文档标题含中文时，中文只进正文标题，文件名用英文短横线（`LUM-ARC-001_architecture.md`、`refs/index.md`）。
- 头文件：公共契约头用 `luma_<层>.h`；内部头用 `luma_<层>_internal.h`，避免 `luma_kernels.h` 这种泛名。

## 6. 文档编号规范（LUM-XXX-NNN）

- `LUM-ARC-*` 架构 / `LUM-ENG-*` 工程 / `LUM-RES-*` 科研 / `LUM-PM-*` 项目。
- 三级：`001` 总纲 → `1xx` 设计 → `2xx` 专项 → `3xx` 接口/体系。
- 单一权威：分层裁决唯一在 `LUM-ARC-101`；理论命题编号唯一在 `theory/state-cache/`（P0–P5），其余推导文档引用同一编号，禁止另立 `§1–§22` 平行体系。

## 7. 测试树命名

- C 测试统一放 `tests/c/`，Python 测试统一放 `tests/python/`（已落地，2026-09）。`theory/*/verify/` 保留为推导附属脚本，正式 CI 以 `tests/` 为准。
- 命题对应注释固定引用编号（`P1/P2/...`），2-ulp 阈值用共享常量 `LUMA_ULP32 = 2^-23`，禁止在多处硬编码 `1.1920928955078125e-7`。

## 8. 无魔法数字（强制）

容差/阈值必须具名（已落地，2026-09）：`LUMA_TERNARY_NEAR_ZERO_SCALE = 1e-12f`、`LUMA_JACOBI_CONVERGE_TOL = 1e-24`、`LUMA_JACOBI_DIVERGE_TOL = 1e-20`、`LUMA_JACOBI_ROTATE_EPS = 1e-15`、`LUMA_SVD_SINGULAR_EPS = 1e-15`、`LUMA_ULP32 = 2^-23`。禁止在函数体/测试体内散落裸数字。

## 9. 落地顺序（不破坏语义）

1. 先定项目身份口径（§0）并记录，冻结为唯一写法。
2. 头拆分（LUM-ARC-101 Phase B）：抽 `include/luma_kv.h`，消除 algorithm→kernel include。
3. 符号/文件重命名按 §3/§5 批量执行（`git mv` + 全仓替换符号，一次一提交）。
4. 测试树合并（§7），跑 `ctest`/`pytest` 全绿后再进下一步。
