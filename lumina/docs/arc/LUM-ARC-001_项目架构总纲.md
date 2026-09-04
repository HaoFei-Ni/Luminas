# LUM-ARC-001 项目架构总纲

- 状态：**骨架（待评审）**
- 关联：`luminas-arch-skill` · `LUM-ARC-101` · `non-goals.md`
- 对应 skill：`.cursor/skills/lumina/luminas-arch-skill/SKILL.md`（本域所有 `LUM-ARC-*` 同源）

## 裁决与文档归属

- 分层唯一裁决点：`../arc/LUM-ARC-101`；四层/三层之争在此收敛，其余 `LUM-ARC-*` 只扩展、不另立模型。
- 文档所在：`lumina/docs/arc/`（自本文件向上两级即 `lumina/` 内容区）。

## 身份

Luminas 是 **原创架构项目**：一套新的无损 KV-cache 压缩机制——不是量化、剪枝、驱逐或低秩近似。仓库内 SpikingBrain2.0 等上游树为**只读技术参考**，非 fork 目标。

## 核心主张

- 无损 = 通过 `research-skill` 三级门槛后才可声称（numeric → model PPL → task）。通过前一律称 **candidate lossless path**，报告真实数字。
- 长上下文是原生 cache + hybrid attention 设计的属性，不靠 RoPE/YaRN/ALiBi 扩展等外部机制。

## 分层总纲

物理分层（algorithm / kernel / wrapper 三层目录 vs Kernel / Binding / Scheduler / Infra 四层职责）的唯一裁决点是 **LUM-ARC-101**。本总纲只锁定原则：

- `lumina/` 是唯一原创代码目录（见 "源码隔离"）。
- 平台无关的压缩数学不进 Python、不进绑定层。

## 源码隔离

- 原创代码一律落 `lumina/`。
- `spb2/`、`spb2vl/`、`spb2_vllm/`、`MoBA/`、`flash-linear-attention_dev/`、`run_model/`：**只读参考**。
- 禁止"就地补丁上游使其成为 Luminas"；禁止把其符号混入 `luma_*` 库。
- 引用的 SOTA / 基线与负面控制（量化、驱逐、低秩）只作为实验对照，见 `LUM-RES-101`。

## 非目标（摘要）

完整拒绝清单见技能 `references/non-goals.md`。摘要：

- 不以 GPTQ/AWQ/HQQ/量化/剪枝/低秩作为产品路径。
- 不把 `flash-attn`、官方 Mamba 当作 Luminas 本体。
- 不以"zero degradation / bit-exact with FP16"写作 lossless 结论。

## 里程碑挂靠

发布 / 里程碑 → `lumina/docs/pm/LUM-PM-001_项目版本与里程碑`。
