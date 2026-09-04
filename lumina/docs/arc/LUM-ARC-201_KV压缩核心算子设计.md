# LUM-ARC-201 KV 压缩核心算子设计

- 状态：**计划（尚未撰写）**
- 关联：`LUM-ARC-001` / `LUM-ARC-101` · `LUM-ENG-301`（L5 无损数值门槛）· `LUM-RES-001`（无损定义）
- 对应 skill：`luminas-arch-skill`（身份）→ `eng-standard-skill`（实现与测试）

## 计划覆盖内容

- 无损 KV 压缩/解压核心算子的候选路径与设计约束
- 与 `luminas/theory/` 中闭合框架的对应关系
- 算子复杂度的公式化声明（FLOP / 峰值字节，供工程 L4 与实验 Phase 1 校验）

## 撰写前必读

1. `luminas-arch-skill/references/non-goals.md`（禁止以量化/驱逐/低秩为产品路径）
2. `research-skill` 的 canonical lossless 定义（三级门槛）
3. `lumina/theory/state-cache/` 既有推导
