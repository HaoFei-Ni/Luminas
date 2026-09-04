# LUM-PM-001 项目版本与里程碑

| 字段 | 内容 |
|:---|:---|
| 状态 | 草案 |
| 版本 | 1.0 |
| 日期 | 2026-09-05 |
| 权威技能 | —（聚合 arc / eng / res） |
| 关联文档 | `LUM-ARC-001` · `LUM-ENG-001` · `LUM-RES-001` |

## 1. 目的

记录版本规则与里程碑出口门禁。每个里程碑须绑定交付物对应的 `LUM-*`、技能门禁与 commit。

## 2. 里程碑

| 里程碑 | 目标 | 出口门禁 | 绑定 commit | 状态 |
|---|---|---|---|---|
| M0 树与门禁落地 | 目录 / 文档 / 技能体系生效 | 文档编号齐备；技能命名 `lumina-{arc,eng,res}-skill` 闭环；GPU 档位 S=4/M=24/L=80 | — | 进行中 |
| M1 候选无损路径 | 产品编解码可测 + 理论 F1–F7 E 层绿 | L1–L3 绿；F1–F7 E 层 exit 0；lab log 锁定套件 | — | 规划 |
| M2 … | （待填） | | | |

## 3. 版本规则

- 采用语义化版本（SemVer）。
- Release 条件：工程门禁绿（`lumina-eng-skill` Merge bar）+ 研究报告绑定 commit hash（`lumina-res-skill` Reproducibility）。
- 未过三级无损门的发布物不得在发行说明中使用「无损 / lossless」字样。
