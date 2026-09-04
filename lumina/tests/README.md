# lumina/tests

测试树对齐 `LUM-ENG-001` 与 `lumina-eng-skill/references/test-matrix.md`。属 **Engineering** 平面（见 `lumina/README.md` 四平面）。

## 布局

| 路径 | 说明 |
|---|---|
| `c/test_luma_kv.c` | 产品 L1 / L2 / L5（2-ulp、恒等 roundtrip） |
| `c/test_luma_baseline.c` | 有损基线 L1 / L2 |
| `python/checks/` | 门禁单元测试（镜像 `tools/checks/`） |
| `python/support/` | cache / metrics 支撑测试 |
| `python/product/` | 绑定 / 内核产品用例 |
| `python/conftest.py` · `helpers.py` · `baselines/` | pytest 共享夹具与 L4 基线 |
| `reports/` | 质量门禁产物（`complexipy.json`、`quality-gate.md` / `.json`；gitignore） |

## 理论轨道（不在本目录）

| 路径 | 说明 |
|---|---|
| `lumina/theory/state-cache/verify/verify-degeneration.py` | 表征坍缩 F1–F7 |
| `check_identity.py` | 遗留恒等脚手架，非 F 门 |

GPU 档位（L4）：**S = 4 GB / M = 24 GB / L = 80 GB**。

## 运行（在 `lumina/` 目录）

```bash
uv run pytest
uv run pytest -m "not native and not cuda"
uv run pytest -m "native or l5"
HYPOTHESIS_PROFILE=ci uv run pytest -n auto --junitxml=.cache/pytest/junit.xml
uv run pytest --cov --cov-report=term-missing
uv run python -m tools.run_quality_gate
```

C 测试：

```bash
ctest --test-dir outputs/build/lumina --output-on-failure
```

构建入口：`lumina/CMakeLists.txt`（superproject）；产物 `_luma_native` / `_luma_cuda` 落在 `outputs/build/lumina/wrapper`。
