# EXP-001 — Bit-exact KV RLE（论文级无损·算子重构）

| 字段 | 内容 |
|:---|:---|
| 方法 | `KV-ENC-CANDIDATE-1` 精确 f32 游程编码 |
| Level 1 | `artifacts/l1_error_hist.json`（`verify_l1_archive.py`） |
| Level 2/3 | 恒等引理（`lab_log.md`）；经验套件待模型 harness |
| 权威 | `LUM-RES-001` §2.1 · `lumina-res-skill` |

```powershell
cd lumina
uv run python -m tools.run_build --test
uv run python experiments/EXP-001_kv-rle-bitexact/verify_l1_archive.py
```
