# verify

对着 [framework](../framework.md) 命题编号做的小规模核验，不是论文实验。

| 脚本 | 对着 | 做什么 |
|---|---|---|
| `check_identity.py` | P1 / P2（当前恒等实现） | 检查 2-ulp 定义与恒等重构；实现换成真 Enc/Dec 后应继续失败或改断言 |

规则：

- 每个断言注释里写 `P1` / `P2` / …，与 framework 同一编号。
- 只放定点算例或符号检查。WikiText / RULER / 五种子正式实验在 `lumina/research/`。
- 通过本目录 **不等于** 无损。P3 未证、三级门未归档之前，结论只能写「候选」。
