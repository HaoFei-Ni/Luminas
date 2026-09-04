# LUM-ENG-001 工程与测试总规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 草案 |
| 版本 | 1.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-eng-skill` |
| 关联文档 | `LUM-ENG-101` · `LUM-ENG-201` · `LUM-ENG-301` · `LUM-ENG-401` · `references/test-matrix.md` |

## 1. 目的

汇总工程侧约定与测试入口。硬性条款以 `lumina-eng-skill/SKILL.md`（物理三层、零循环热路径、结构度量、编码规则）及 `references/test-matrix.md` 为准；本文件不重复展开。

## 2. 语言与符号（摘要）

| 栈 | 约定 |
|---|---|
| C99 参考核 | 仅 C99；导出 `luma_*`；文件内 `static`；宏 `LUMA_*`；显式分配与边界检查；公共 API 返回 `int`（不用 `errno`） |
| CUDA | 导出 `luma_cuda_*`；grid/block 为参数；热路径无 bank 冲突；每次 runtime API 与 launch 后检查错误；数值对齐全 C99 参考的 L1/L5 |
| Triton | 导出 `luma_triton_*`；tile 为参数；相对 CUDA twin 均值延迟 ≤ 1.11× |
| Rust（可选） | 每个 `unsafe` 有 safety 注释；库路径禁止 `unwrap` / `expect` |
| Python | 仅编排 / wiring / 测试 / 循环控制；**无**算子与 KV 编解码数学；全标注、`mypy` 干净 |
| pybind11 | 仅 marshal / 校验 / 异常映射；绑定 `.cpp` 内无数值算法；核启动前释放 GIL |

细则见 `LUM-ENG-101`。

## 3. GPU 显存档位

| Tier | VRAM | 默认职责 |
|---|---|---|
| S | **4 GB** | 功能验证与 degrade 路径 |
| M | 24 GB | 默认研究 GPU |
| L | 80 GB | 128k / 大 batch |

OOM 时必须 degrade（缩小 tile），禁止静默 abort。无损 KV 路径上的 degrade 仍须通过 L5。

## 4. 测试体系

| 轨道 | 编号 | 说明 |
|---|---|---|
| 产品 | L1–L5 | 算子 / 绑定 / 编解码；L5 仅限压缩 / 解压 / 残差路径 |
| 理论 | F1–F7 | `theory/state-cache/verify/verify-degeneration.py`；与 L1–L5 正交 |

覆盖率、2-ulp 数值门、L4 协议、合并门槛：一律以 `lumina-eng-skill/references/test-matrix.md` 为准。F 系列不替代 L5，亦不授予论文「无损 KV」。

质量门禁编排与报告制品见 `LUM-ENG-301` §3；真值源 `lumina/quality-gate.toml`；产物落在 `tests/reports/`。

## 5. 相关编号

| 文档 | 主题 |
|---|---|
| `LUM-ENG-101` | 命名与编码 |
| `LUM-ENG-201` | 构建与依赖 |
| `LUM-ENG-301` | 测试工具链入口 |
| `LUM-ENG-401` | 全量质量评审与整改路线图；目标阈值见 `quality-gate.l5-target.toml` |
