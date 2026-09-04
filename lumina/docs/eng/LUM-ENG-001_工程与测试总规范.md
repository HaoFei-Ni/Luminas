# LUM-ENG-001 工程与测试总规范

- 状态：**骨架（待评审）**
- 关联：`eng-standard-skill`（SKILL.md + `references/test-matrix.md`）
- 对应 skill：`.cursor/skills/lumina/eng-standard-skill/SKILL.md`

## 权威分层

`eng-standard-skill/SKILL.md` 正文第 1 章为**最高优先级工程规范**（架构级强制标准：三层正交分层、零循环零递归、结构度量、极致性能、正确性、架构执行原则）。本文档不重复其条目，只做工程侧的汇总与指针。

## 语言与符号约定（摘要）

- C99 参考核：C99 only；导出符号 `luma_*`，文件内 `static`，宏 `LUMA_*`；显式分配 + NULL/边界检查；公共 API 返回 `int` 错误码，不用 `errno`。
- CUDA：`luma_cuda_*`；grid/block 为参数非字面量；共享内存无 bank 冲突；每次 runtime API 后检查错误；与 C99 参考在 L1/L5 数值门槛下一致。
- Triton：`luma_triton_*`；tile 为参数；与 CUDA twin 对比 ≤ 1.11× 均值延迟。
- Rust（可选）：每个 `unsafe` 有 safety 注释；库路径不 `unwrap`。
- Python：只做编排/wiring/测试/循环控制，**无算子与 KV 编解码数学**；全标注、mypy clean。
- pybind11：只做 marshal/校验/异常映射，绑定 `.cpp` 内无数值算法；释放 GIL。

## GPU 显存分层

| Tier | VRAM | 默认职责 |
|---|---|---|
| S | 8 GB | 功能 + degrade 路径 |
| M | 24 GB | 默认研究 GPU |
| L | 80 GB | 128k / 大 batch |

OOM 必须 degrade（更小 tile），不静默 abort。

## 测试体系（指针）

L1–L5 分层、覆盖率门槛、数值门槛（2 ulp）、benchmark 协议：全部以 `references/test-matrix.md` 为准。

## 相关编号

- 各语言细则 → `LUM-ENG-101`
- 构建/依赖 → `LUM-ENG-201`
- 测试工具链与 CI → `LUM-ENG-301`
