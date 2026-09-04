# lumina/ — Luminas 唯一内容区（源码 + 文档 + 实验归档）

`docs/`、`refs/`、`experiments/` 均收纳于此，不再存在于仓库根。
分层裁决见 `docs/arc/LUM-ARC-101`。仓库级导航见根 `README.md`。

| 目录 | 职责 | 现状 |
|---|---|---|
| `algorithm/` | 平台无关 ANSI C 压缩/解压数学（纯逻辑） | 已启用（`luma_kv_ref.c` / `luma_kv_cpu.c`） |
| `kernel/` | C-ABI 头、CUDA/CPU 算子、有损基线 | 现有代码在此（C99 + baseline + CUDA） |
| `wrapper/` | 对外 API / pybind 绑定 / 封装 | 已启用（`luma_bind_*.cpp`） |
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

## 分层迁移记录（LUM-ARC-101 Phase A，2026-09 已执行）

| 文件 | 迁移去向 | 说明 |
|---|---|---|
| `kernel/luma_kv_ref.c` / `kernel/luma_kv_cpu.c` | → `algorithm/` | 平台无关压缩参考/算法实现（C99） |
| `kernel/luma_bind_native.cpp` / `kernel/luma_bind_cuda.cpp` | → `wrapper/` | pybind11 marshal，无数值算法 |
| `kernel/baseline/*`、`kernel/luma_*kernels.h`、`kernel/test/*` | 留在 `kernel/` | 基线 / C-ABI 头 / 测试 |

> 迁移同步了 `kernel/CMakeLists.txt` 源路径（`../algorithm/`、`../wrapper/`）；include 解析仍经 `target_include_directories(luma_cpu PUBLIC <kernel>)`。头文件拆分（Phase B）待办见 `docs/arc/LUM-ARC-101`。
