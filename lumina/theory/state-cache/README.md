# 架构无关的状态缓存压缩

定律级闭合数学框架的工作目录。权威稿是 [framework.tex](framework.tex)；可读副本是 [framework.md](framework.md)。符号核验在 [verify/](verify/)。

**状态：候选路径。** 推导未闭合前不得称无损，不得报压缩比。论文 Method 引用本目录，不另起一套公式。

## 主张（锁定）

1. 对象是**状态缓存**（Transformer 的 KV、SSM 的隐状态、脉冲/事件状态等），不绑定某一骨干。
2. 产品路径是可逆/可控误差的压缩，不是量化、驱逐、低秩近似。那些算法只在 `lumina/kernel/baseline/` 作对照。
3. 「无损」只由 `research-skill` 三级门认定：数值 2 ulp、PPL、任务。本目录只负责把数值级写成可核验命题。

## 符号表

| 符号 | 含义 | 约定 |
|---|---|---|
| \(S\) | 未压缩状态缓存 | 行主序，实数，有限 |
| \(T, H, d\) | 序列长、头数、头维 | \(n = T \cdot H \cdot d\) 展平后长度 |
| \(\mathrm{Enc}, \mathrm{Dec}\) | 编码 / 解码 | \(\widehat{S} = \mathrm{Dec}(\mathrm{Enc}(S))\) |
| \(C\) | 压缩表示 | 字节数 \(\lvert C\rvert\) |
| \(\rho\) | 压缩比 | \(\rho = \mathrm{bytes}(S) / \lvert C\rvert\)；恒等实现禁止报 \(\rho\) |
| \(\varepsilon(S)\) | 逐元误差 | \(\lvert \widehat{S}_i - S_i\rvert\) |
| \(\mathrm{ulp}_{32}(x)\) | FP32 单位 |
| 2-ulp 门 | 数值级通过条件 | \(\varepsilon(S_i) \le 2 \cdot 2^{-23} \cdot \max(1, \lvert S_i\rvert)\)，且 \(\ge 99.9\%\) 元满足 |

命题编号（写入 framework 后，核验与测试必须引用同一编号）：

| ID | 命题 | 核验落点 |
|---|---|---|
| P0 | 状态缓存的架构无关定义与接口 | 本文 §P0 |
| P1 | 重构：\(\mathrm{Dec}\circ\mathrm{Enc}\) 在定义域上的误差界 | `verify/` + `luma_kv_ref_copy_f64` |
| P2 | 2-ulp 门与 P1 的包含关系 | `lumina/kernel/test/test_luma_kv.c` L5 |
| P3 | 下游算子（注意力 / 扫描 / 脉冲累积）对 \(\widehat{S}\) 与 \(S\) 的等价条件 | framework 推导；未证之前不做无损宣称 |
| P4 | 时间、字节随 \(T\) 的复杂度 | framework；实现对照 `luma_kv_*` |
| P5 | 闭合：无损区的失效边界（长度、动态范围、非有限输入） | verify + 实验室日志 |

## 与 kernel 的挂钩

| 理论对象 | C-ABI | 文件 |
|---|---|---|
| 预言机 \(S \mapsto S\)（FP64） | `luma_kv_ref_copy_f64` | `lumina/kernel/luma_kv_ref.c` |
| \(\mathrm{Enc}\) | `luma_kv_encode_f32` | `lumina/kernel/luma_kv_cpu.c` |
| \(\mathrm{Dec}\) | `luma_kv_decode_f32` | 同上 |
| 有损对照 | `luma_baseline_*` / `luma_cuda_baseline_*` | `lumina/kernel/baseline/` |
| L1/L2/L5 | `test_luma_kv` | `lumina/kernel/test/test_luma_kv.c` |

公式落地时**只改 encode/decode 函数体**，不改预言机，不把 baseline 抬回产品路径。

## 目录

```text
lumina/theory/state-cache/
  README.md           本页
  framework.tex       权威推导稿
  framework.md        同结构可读稿
  verify/             对着 P1–P5 的符号/小规模数值核验
```
