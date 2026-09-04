# 正式文档归档

本文档库按 **域（arc / eng / res / pm）× 编号（001 总纲 → 1xx 设计 → 2xx 专项 → 3xx 接口/体系）** 组织。每个编号对应唯一权威技能；正文以 `.cursor/skills/lumina/lumina-{arc|eng|res}-skill` 为准，本文档库为可引用的正式副本与扩展。

## 编号体系

| 域 | 总纲 | 子文档 | 权威技能 |
|---|---|---|---|
| `arc/` 架构 | LUM-ARC-001 | 101 分层 / 201 算子 / 301 接口 | `lumina-arc-skill` |
| `eng/` 工程 | LUM-ENG-001 | 101 编码 / 201 构建 / 301 测试 | `lumina-eng-skill` |
| `res/` 科研 | LUM-RES-001 | 101 消融 / 201 数据集 / 301 论文 | `lumina-res-skill` |
| `pm/` 项目 | LUM-PM-001 | 里程碑与版本 | — |

技能冲突优先级：`lumina-arc-skill` > `lumina-eng-skill` > `lumina-res-skill` > Orchestra。

## 文档状态用语

| 状态 | 含义 |
|---|---|
| **生效** | 可引用的现行规范；变更须同步技能与关联文档 |
| **草案** | 内容可用，待终审签字后升格为生效 |
| **计划** | 仅规定范围与约束；细节以权威技能 references 为准，正文待补 |

## 写作规则

1. **总纲（-001）为域内唯一入口**；派生文档只扩展，不另立平行体系。
2. 每篇文档须含元信息表：状态、版本、日期、权威技能、关联文档。
3. 分层与源码归属以 `arc/LUM-ARC-101` 为唯一裁决点（职责四层 vs 物理三层）。
4. 实验结论不写入 `docs/`：协议与 lab log → `../research/`；归档产物 → `../experiments/`。
5. 「无损 / lossless」未通过 `lumina-res-skill` 三级门前，一律写作 **candidate lossless path**。
6. GPU 档位统一为 **S = 4 GB / M = 24 GB / L = 80 GB**（见 `lumina-eng-skill`）。
