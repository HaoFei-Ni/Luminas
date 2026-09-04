# papers/ — 参考论文

按领域归档。当前为空（待建）。

建议目录（按 `research-skill` / `luminas-arch-skill` 引用面）：

- `kv-compression/` — 无损/有损 KV 压缩、量化类基线（KIVI、KVQuant、GPTQ/AWQ 作对照）
- `eviction-sparse/` — H2O、SnapKV、StreamingLLM（驱逐类 SOTA 对照）
- `lowrank/` — 低秩 KV 方法（基线类）
- `attention-ssm/` — Falcon-H1、Mamba-3、FlashAttention（混合架构参考）
- `event-spiking/` — SpikingBrain2.0、脉冲/事件驱动（只读技术参考）
- `looped/` — Ouro 等循环深度（参考思想）

## 每条目字段

```text
标题 / 作者 / 年份 / 出处
BibTeX → 见 [../参考文献索引.md](../参考文献索引.md)（统一 bib 库）
PDF 链接或本地路径
Luminas 角色：baseline | reference idea | read-only study | …
```

## 约束

- 复制上游代码进 `lumina/` 是被禁止的（见 `luminas-arch-skill/references/non-goals.md`）；`papers/` 仅存资料。
