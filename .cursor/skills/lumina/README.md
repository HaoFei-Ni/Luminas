# Luminas skills

Project Agent Skills under `.cursor/skills/lumina/`。与 `lumina/docs/{arc,eng,res}/` 及 `LUM-{ARC,ENG,RES}-*` 一一对齐。

| 目录 / `name` | 域 | 文档前缀 | 职责 |
|---|---|---|---|
| `lumina-arc-skill` | 架构 | `LUM-ARC-*` | 身份、非目标、职责分层、源码隔离 |
| `lumina-eng-skill` | 工程 | `LUM-ENG-*` | 编码、构建、L1–L5 / F1–F7 测试矩阵 |
| `lumina-res-skill` | 科研 | `LUM-RES-*` | 实验、三级无损门、论文骨架 |

**优先级：** `lumina-arc-skill` > `lumina-eng-skill` > `lumina-res-skill` > Orchestra。

## 命名

模式：`lumina-{arc|eng|res}-skill`（kebab-case）。目录名与 YAML `name` 一致。

废弃别名（禁止再用）：`luminas-arch-skill`、`eng-standard-skill`、`research-skill`。

## 统一约定

| 项 | 值 |
|---|---|
| GPU 档位 | S = 4 GB / M = 24 GB / L = 80 GB |
| 无损用语 | 未过三级门 → **candidate lossless path** |
| 理论判据 | F1–F7（`theory/state-cache/`） |
| 产品测试 | L1–L5（与 F 系列正交） |

## SKILL.md 共用结构

1. YAML frontmatter（`name`、`description`、`metadata`）
2. 标题与 owns / does-not-own
3. Priority
4. When to use / Do not use
5. 域规则
6. Related documents（`LUM-*`）
7. Additional resources

## 两套分层视图（勿混淆）

| 视图 | 所有者 | 栈 |
|---|---|---|
| 职责（运行时角色） | `lumina-arc-skill` | Kernel → Binding → Scheduler → Infra |
| 物理（源码树） | `lumina-eng-skill` | `algorithm/` → `kernel/` → `wrapper/` |

冲突裁决：`lumina/docs/arc/LUM-ARC-101`。
