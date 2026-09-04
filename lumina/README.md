# lumina/ — Luminas 唯一内容区（源码 + 文档 + 实验归档）

`docs/`、`refs/`、`experiments/` 均收纳于此，不再存在于仓库根。
分层裁决见 `docs/arc/LUM-ARC-101`。仓库级导航见根 `README.md`。

| 目录 | 职责 | 现状 |
|---|---|---|
| `algorithm/` | 平台无关 ANSI C 压缩/解压数学（纯逻辑） | **规划中（空）** |
| `kernel/` | CPU/CUDA 算子、并行映射、pybind 绑定入口 | 现有代码在此（C99 + baseline + CUDA + bind） |
| `wrapper/` | 对外统一 API / 封装层（C-ABI、错误与内存管理透明化） | **规划中（空）** |
| `theory/` | 架构无关方法笔记、闭合框架、推导 | 现有（`state-cache/`） |
| `research/` | 实验协议、lab log、官方案例运行 | **规划中（空）** |
| `tests/` | Python 测试（pytest） | 现有 `tests/test_luma_kernels.py` |
| `docs/` | 正式文档（LUM-* 编号归档：arc/eng/res/pm） | 骨架已建（2026-09） |
| `refs/` | 外部参考文献与规范（papers/ specs/） | 骨架已建（2026-09） |
| `experiments/` | 实验归档产物 `EXP-YYYYMMDD-XXX/` | 骨架已建（2026-09） |

## 分层模型冲突收敛

- 职责 4 层（Kernel/Binding/Scheduler/Infra）见 `luminas-arch-skill`。
- 物理 3 层（algorithm/kernel/wrapper）见 `eng-standard-skill` 最高优先级章节。
- **两者归属口径以 `docs/arc/LUM-ARC-101` 为唯一裁决点**；未裁决前新代码默认落现有 `kernel/`，不新建散目录。

## 当前文件归类规划（kernel/ 内，待 LUM-ARC-101 冻结后执行迁移）

| 现有文件 | 规划归属 | 说明 |
|---|---|---|
| `luma_kv_ref.c` / `luma_kv_cpu.c` | `algorithm/` | 平台无关压缩参考数学（C99） |
| `baseline/*.c`、`baseline/*.cu` | `kernel/baseline/`（或 `kernel/` 内 baseline） | 有损基线对照，非产品路径 |
| `luma_bind_native.cpp` / `luma_bind_cuda.cpp` | `wrapper/`（绑定层） | pybind11 marshal，无数值算法 |
| `luma_cuda_kernels.h` / `luma_kernels.h` | `kernel/` | 算子接口头 |

> 迁移必须同步 `kernel/CMakeLists.txt` 路径与 skill `paths`；禁止一次性大挪移。
