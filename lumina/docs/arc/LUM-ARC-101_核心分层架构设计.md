# LUM-ARC-101 核心分层架构设计

- 状态：**骨架（待评审）— 本文件是"四层职责"与"三层物理目录"冲突的唯一裁决点**
- 关联：`LUM-ARC-001` · `luminas-arch-skill` · `eng-standard-skill`

## 背景：两套模型并存

仓库存在两套被不同技能引用的分层模型，本文件负责收敛，禁止任何新代码/新目录绕开本裁决自定归属：

| 视图 | 来源 | 内容 |
|---|---|---|
| 职责视图（4 层） | `luminas-arch-skill`（拥有 source tree） | Kernel → Binding → Scheduler → Infra |
| 物理目录视图（3 层） | `eng-standard-skill` 最高优先级章节 | `algorithm/` → `kernel/` → `wrapper/` |

## 裁决原则（初稿，待评审）

1. **两者不是同一分类轴**：4 层回答"谁做什么职责"；3 层回答"代码放哪个物理目录"。
2. **物理目录规划**：
   - `lumina/algorithm/` — 平台无关 ANSI C 压缩/解压数学（纯逻辑、无系统 API、无 CUDA）。
   - `lumina/kernel/` — CUDA / CPU 算子、并行映射、`cuda*` 适配；只调用 algorithm 的纯逻辑，不重实现本体。
   - `lumina/wrapper/` — 对外 C-ABI / pybind11 绑定、内存与错误处理封装、上层稳定接口。
   - `lumina/theory/` → 方法研究（架构无关笔记），保留现状，归研究模块。
3. **Binding / Scheduler / Infra 职责**不因 3 层目录而消失：绑定落 `wrapper/` 或独立绑定 target；Python 调度仍只做编排，不做算子/KV 数学（见 `LUM-ENG-101`）。
4. 任何迁移须同时更新：`lumina/kernel/CMakeLists.txt` 目标路径、`eng-standard-skill` 的 `paths`、本文件。

## 层间规则

- 禁止反向依赖与同层循环依赖。
- 层头文件只暴露最小接口，不含实现。
- 所有迁移先出迁移单（commit 粒度），禁止一次性大挪移。

## 待办

- [ ] 三技能 owner 会签本裁决
- [ ] 冻结 `algorithm/`、`wrapper/` 首批文件清单
- [ ] 迁移并同步 CMake / 测试 / skill `paths`
