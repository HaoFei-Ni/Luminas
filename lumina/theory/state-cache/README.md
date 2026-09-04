# 深度神经网络表征坍缩统一理论

| 字段 | 内容 |
|:---|:---|
| 权威稿 | [framework.tex](framework.tex) |
| 排版 PDF | [framework.pdf](framework.pdf) |
| 可读副本 | [framework.md](framework.md) |
| 数值核验 | [verify/](verify/) |
| 工程挂靠 | `lumina-eng-skill` · F1–F7（`references/test-matrix.md`） |

**三级串联：** L0 精确秩亏判定 → L1 深度表示坍缩 → L2 训练动力学秩坍缩；公共阈值 \(\tau\) 闭合为
\[
D(k(\tau))=\sum_{i>k(\tau)}\sigma_i^2.
\]

**状态：** 公理域内 F1–F7 核验零违例（\(\mathrm{SEED}=20240904\)）。本目录为谱秩结构闭合理论，**不是**产品路径上的「无损 KV」宣称；后者仅由 `lumina-res-skill` 三级门认定。

## 主张（锁定）

1. 对象为任意层的**层矩阵**（权重 / 特征 / 内容）及其 SVD 谱；退化由谱多重集度量。
2. 「0 级退化」专指奇异值精确为零的 0/1 判定；与 \(k\) 阶近似低秩严格区分，二者由公共阈值 \(\tau\) 串联。
3. 表示坍缩由**线性秩亏**严格承载；非线性激活可部分增秩，不解除上游线性秩帽。
4. 训练侧结论依赖公理 A4（核范数谱损失）；非谱损失动力学不在本框架内宣称闭式。

## 权威关系

| 产物 | 角色 |
|---|---|
| `framework.tex` | **单一权威源**（含证明链与核验器附录） |
| `framework.pdf` | 由 tex 编译的排版定稿 |
| `framework.md` | 同结构可读副本；冲突时以 tex 为准 |
| `verify/verify-degeneration.py` | F1–F7 可运行核验器（与 tex 附录一致） |

## 判据对照

| ID | 内容 | 核验 |
|---|---|---|
| F1–F7 | 谱隙 / EYM / Weyl–Mirsky / Sylvester / ReLU 边界 / SVT / 临界时间 | `verify/verify-degeneration.py` |
| L5（产品） | 2-ulp 编解码 | `lumina/tests/c/test_luma_kv.c`（与 F 系列正交） |

完整公理、引理与定理见 [framework.md](framework.md) / [framework.tex](framework.tex)。

## 目录

```text
framework.tex             权威推导稿（含核验器附录）
framework.pdf             排版定稿
framework.md              同结构可读副本
verify/
  verify-degeneration.py  F1–F7 主核验器
  check_identity.py       遗留恒等脚手架（非 F 门）
  README.md
```
