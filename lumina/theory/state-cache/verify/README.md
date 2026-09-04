# verify

对着权威稿 [framework.tex](../framework.tex) / 可读副本 [framework.md](../framework.md) 的可证伪判据 F1–F7 做小规模核验；**不是**论文级任务实验。

| 脚本 | 对着 | 说明 |
|---|---|---|
| `verify-degeneration.py` | F1–F7（主入口） | E 层精确算例；`--mc` 大样本；`--data` 契约 `degeneration-v1` |
| `check_identity.py` | （遗留） | 旧恒等 Enc/Dec + 2-ulp；**不是** F 系列结果 |

## 用法

```bash
python verify-degeneration.py
python verify-degeneration.py --mc
python verify-degeneration.py --data FILE
python verify-degeneration.py --print-template
```

固定种子：`SEED=20240904`。产出：`verify-degeneration-real-results.txt`、`verify-degeneration-mc-results.txt`。

## 规则

1. 断言引用 **F1–F7**（或定理 / 引理编号），与 `framework.tex` 一致。
2. 仅定点算例、扰动界与闭式对照；正式任务实验在 `lumina/research/`。
3. 本目录通过 **不等于** 产品「无损 KV」。无损仅由 `lumina-res-skill` 三级门认定。
4. 完整核验器亦可从 [framework.tex](../framework.tex) 附录抽出；以本目录 `.py` 为可运行副本。

工程矩阵挂靠：`lumina-eng-skill/references/test-matrix.md`（Theory track）。
