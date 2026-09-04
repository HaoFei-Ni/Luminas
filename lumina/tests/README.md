# lumina/tests

测试树（LUM-ENG-001 / eng-standard test-matrix）：

- `c/`：C 测试（ctest）
  - `test_luma_kv.c` — 产品路径 L1/L2/L5（2-ulp 门、恒等 roundtrip）
  - `test_luma_baseline.c` — 有损基线 L1/L2
- `python/`：Python 测试（pytest）
  - `conftest.py` — Hypothesis profile + `luma_native` / `luma_cuda` fixture
  - `helpers.py` — 共享辅助（`ulp2_limit`）
  - `test_quality_metrics.py` — 纯 Python L1/L2（无扩展也可绿）
  - `test_luma_kernels.py` — L2/L3/L5 绑定门（需已构建 `_luma_native`）

## 运行（在 `lumina/` 目录）

```bash
# 本地默认：纯 Python 必绿；native/cuda 未构建时自动 skip
uv run pytest

# 仅纯 Python
uv run pytest -m "not native and not cuda"

# 仅绑定/无损门（需先 cmake 构建 pybind 模块）
uv run pytest -m "native or l5"

# CI 确定性档（Hypothesis derandomize + 并行 + JUnit）
HYPOTHESIS_PROFILE=ci uv run pytest -n auto --junitxml=.cache/pytest/junit.xml

# 覆盖率（quality_metrics 公共面）
uv run pytest --cov --cov-report=term-missing
```

C 测试：

```bash
ctest --test-dir outputs/build/lumina --output-on-failure
```

构建入口：顶层 `lumina/CMakeLists.txt`（superproject），产物 `_luma_native` /
`_luma_cuda` 落在 `outputs/build/lumina/wrapper`（已写入 `pythonpath`）。
