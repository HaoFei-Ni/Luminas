# LUM-ARC-201 KV 压缩核心算子设计

| 字段 | 内容 |
|:---|:---|
| 状态 | 生效（最小契约） |
| 版本 | 0.2 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-arc-skill`（身份）→ `lumina-eng-skill`（实现与测试） |
| 关联文档 | `LUM-ARC-001` · `LUM-ARC-101` · `LUM-ARC-301` · `LUM-ENG-301` · `LUM-RES-001` |

## 1. 范围

1. 产品路径无损 KV 压缩 / 解压核心算子的**候选**设计约束与 ABI 挂钩点。
2. 与 `lumina/theory/state-cache/`（F1–F7）的关系：谱侧理论**不等于**产品 Enc/Dec。
3. 算子复杂度声明槽位（FLOP / 峰值字节），供工程 L4 与实验 Phase 1 引用同一公式 ID。

## 2. 产品算子合同（现行 ABI）

| 符号 | 角色 | 现行实现 | 允许演进 |
|---|---|---|---|
| `luma_kv_ref_copy_f64` | FP64 预言机 | 有限输入逐元复制 | **语义冻结**；换压缩器不得改 |
| `luma_kv_encode_f32` | 候选 Enc | 精确 f32 RLE（`KV-ENC-CANDIDATE-1`） | 保持签名；升级公式改函数体 |
| `luma_kv_decode_f32` | 候选 Dec | RLE 展开至长度 `n` | 同上 |

头文件真源：`algorithm/luma_kv.h`。

### 2.1 数值门（工程 L5 / 科研 Level 1）

对重构 `Ŝ` 与预言机对照的有限元素：

`|Ŝ_i - S_i| ≤ 2 · 2^{-23} · max(1, |S_i|)`，且无 NaN/Inf。

人口规则（归档时）：≥ 99.9% 有限元素通过，并保存 log-abs 误差直方图。

### 2.2 明确禁止（产品路径）

不得将下列实现写入 `luma_kv_encode_f32` / `luma_kv_decode_f32` 作为产品：

- GPTQ / AWQ / HQQ / bitsandbytes 等权重量化作 KV「压缩」
- 截断 SVD / 低秩近似作产品压缩机
- token 驱逐 / Streaming 式丢弃作「无损」
- 直接 vendor `flash-attn` / 官方 Mamba 作真源

有损对照一律落在 `kernel/baseline/` 与 `kernel/cuda/`，经 `_luma_baseline` / `_luma_cuda` 导出。

### 2.3 压缩比与无损叙事

恒等占位已退役。RLE 可在重复值上取得 `enc_len < 2n`；ρ 仅可在实验归档中报告。

- **算子重构**：`KV-ENC-CANDIDATE-1` 为 bit-exact；Level 1 归档见 `experiments/EXP-001_kv-rle-bitexact/`。
- **论文级无损**：在 Level 1 PASS 且恒等引理适用时，按 `LUM-RES-001` §2.1 可称「论文级无损（算子重构）」；经验 L2/L3 套件用于防回归与披露，不放宽 L1。

## 3. 公式 ID 槽位（待填真公式）

| ID | 含义 | 状态 |
|---|---|---|
| `KV-ENC-CANDIDATE-0` | 历史恒等 Enc/Dec（已退役） | 退役 |
| `KV-ENC-CANDIDATE-1` | 精确 f32 游程编码 `(value,count)` 对 | **现行** |
| `KV-FLOP-CANDIDATE-1` | 最坏 O(n) 扫描 + O(n) 展开 | 现行（L4 键 `luma_kv_encode_decode_f32`） |
| `KV-BYTES-CANDIDATE-1` | 码流最坏 `2n` 个 float；可压缩时更短 | 现行 |

选型 `KV-ENC-CANDIDATE-1` 时必须同步更新本表、头注释与 L4 `required_score_keys`。

## 4. 与理论 F1–F7

- F 门通过 → 仅证明谱/表征侧命题，**不**自动授予产品「无损」。
- 产品路径引用理论时写「受 F* 启发的候选」，并指向具体 commit 的 `framework.tex`。

## 5. 约束

- 不在本文件重新定义分层（见 `LUM-ARC-101`）。
- 缓冲所有权 / 错误传播见 `LUM-ARC-301`。
- 撰写真公式前必读：`non-goals.md`、三级无损定义、`theory/state-cache/framework.tex`。
