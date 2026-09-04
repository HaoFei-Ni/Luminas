# LUM-ENG-401 全量质量评审与整改路线图

| 字段 | 内容 |
|:---|:---|
| 状态 | 生效（评审交付） |
| 版本 | 1.0 |
| 日期 | 2026-09-05 |
| 基准 commit | `d3120b2` |
| 权威技能 | `lumina-arc-skill` → `lumina-eng-skill` → `lumina-res-skill` |
| 关联 | `LUM-ARC-001/101/201/301` · `LUM-ENG-101/201/301` · `LUM-PM-001` · `quality-gate.l5-target.toml` |

## 0. 专家团主裁决（一句话）

**Engineering 平面（`tools/` + 门禁 + 测试 taxonomy）已超过多数一线研究仓平均水平；Product 平面仍是「可测 ABI 脚手架 + 有损基线」，距 Linux/LLVM/CUDA Toolkit/MKL/PyTorch 级可开源基础组件尚缺真实无损压缩器、接口契约正文、双端性能门与三级无损归档。禁止用质量门禁 PASS 冒充产品「无损」。**

对标口径：分层纯度≈内核子系统边界；门禁≈LLVM lit+clang-tidy；算子≈MKL/cuBLAS 合同；实验≈PyTorch 可复现 CI。

---

## 1. 问题分级清单

### 1.1 致命架构缺陷（阻断「工业级无损 KV」主张）

| ID | 位置 | 问题 | 风险影响 | 与顶级标准差距 |
|---|---|---|---|---|
| **F-A1** | `algorithm/luma_kv_codec.c`；`luma_kv.h` 注释 | 产品 Enc/Dec 为有限性检查后的 **恒等 `memcpy`**，`enc_len == n` | 任何压缩比 / 吞吐 / 「无损压缩」对外表述均为虚假；实验无法进入 L2/L3 | MKL/cuBLAS：无真实算子合同（输入约束、复杂度、误差界） |
| **F-A2** | `docs/arc/LUM-ARC-201`、`LUM-ARC-301`（v0.1 空壳） | 算子设计与层间接口无正文 | 实现无单一真值源；绑定/内核可漂移；社区无法按 ABI 协作 | LLVM/CUDA Driver：接口文档即合同 |
| **F-A3** | 无 `runtime/`（Scheduler）；无 hybrid/SSM/spike 源码 | 职责四层中 Scheduler 与架构叙事中的混合注意力 / 可选脉冲核缺位 | 文档与技能承诺超前于代码；路线图不可验收 | PyTorch：模块树与文档同构 |

### 1.2 严重质量问题（阻断 Merge bar / 双端可信）

| ID | 位置 | 问题 | 风险影响 | 差距 |
|---|---|---|---|---|
| **F-S1** | `tools/checks/performance/workloads.py`；`l4_perf_baseline.json` | L4 仅计时 Python list **saxpy**，与 KV/CUDA 无关 | 「≤2% 回归」对产品无意义；虚假安全感 | CUDA Toolkit / nsys·ncu 工作负载文化 |
| **F-S2** | `[hypothesis]` vs `tests/python/product/` | `ha` profile 5000 examples **未接线**产品 Enc/Dec | 「5 个 9」叙事与覆盖脱节 | Hypothesis 工业用法：配置=执行 |
| **F-S3** | 顶层 `CMakeLists.txt`（CUDA OFF）；无 CUDA ctest/pytest | 双端基线不对等；`fused_decode` 未导出 | GPU 路径回归盲区 | CUDA Toolkit 双路径 CI |
| **F-S4** | `algorithm/luma_kv.h`：`LUMA_ERR_CUDA` | 纯算法契约携带平台错误码 | 分层纯度破口；algorithm 语义污染 | 内核：子系统错误域隔离 |
| **F-S5** | `wrapper/luma_bind_native.cpp` | 产品 KV 与有损 quant/SVD **同模块导出** | 调用方易把基线当产品；命名含 `kv` 的 int8 量化更易误读 | 最小暴露 / 稳定 ABI 分区 |

### 1.3 一般优化点

| ID | 位置 | 问题 | 影响 |
|---|---|---|---|
| **F-G1** | `[c_thresholds]` | 仅行数/循环；**无** eng-skill 声明的圈复杂度 ≤5、if 嵌套 ≤2 机器门禁 | C 热路径腐化可静默进入 |
| **F-G2** | 根 `README.md` L57+ | SpikingBrain2.0 大段营销体与上方 Luminas 身份并置 | 外部贡献者误判 fork 目标 |
| **F-G3** | `kernel/test/` 空；`research/`、`experiments/` 仅 README | 四平面 Research ops 未运转；空目录噪音 | 「看目录即知架构」打折 |
| **F-G4** | `quality-gate.toml` / ENG-101 注释残留 `ci_quality_gate` 等旧名 | 真值源信任侵蚀 | 文档=代码 原则 |
| **F-G5** | `Makefile`：`SHELL := /bin/bash` | 原生 Windows 开发体验弱 | 跨平台工程惯例 |
| **F-G6** | `pyproject` coverage `fail_under=80` 仅 `tools.support.metrics` | 覆盖率门禁几乎不保护产品 | PyTorch 式表面覆盖文化 |

### 1.4 建议提升项

| ID | 建议 | 对标 |
|---|---|---|
| **F-R1** | CI 增加 ASAN/UBSAN；CUDA compute-sanitizer 可选车道 | LLVM / CUDA Toolkit |
| **F-R2** | `clang-tidy` + `-Wall -Wextra -Werror` 正式进 `make quality` | Linux / LLVM |
| **F-R3** | 符号更名：`luma_cuda_kv_quant_int8` → `luma_cuda_baseline_kv_int8`（与文件意图对齐） | 命名即文档 |
| **F-R4** | 首次 `EXP-001` lab log + 锁定套件哈希（即使仍为 candidate） | `lumina-res-skill` |
| **F-R5** | 根 README 上游营销迁至 `refs/` 或独立 `UPSTREAM.md` | 子系统 README 清晰度 |

### 1.5 明确「非缺陷」（合规通过项）

| 项 | 判定 |
|---|---|
| 未把 GPTQ/AWQ/HQQ/剪枝/FlashAttention 做成产品路径 | **合规**（non-goals 执行到位） |
| 有损 quant/SVD/int8 位于 `kernel/baseline` / `kernel/cuda` | **允许**（基线类）；须保持叙事与导出隔离 |
| 物理三层 `algorithm/`→`kernel/`→`wrapper/` 冻结 | **正确**；本路线图 **禁止** 改名或塞入 `src/lumina` |
| `theory/` 独立于 `research/` | **正确**（F1–F7 权威路径） |
| Engineering `checks/reporting/support` taxonomy | **达标**；停止第三轮缩写↔全称改名 |

---

## 2. 全量整改方案（按问题 → 措施 → 验收）

### F-A1 真压缩器落地（候选无损路径）

| 步骤 | 措施 | 验收标准 |
|---|---|---|
| A1.1 | 在 `LUM-ARC-201` 选定 **一条** 候选公式（禁止同时落地量化/低秩作产品） | 文档「生效」；含输入域、码流布局、复杂度、与 F1–F7 **非等同**声明 |
| A1.2 | 仅改 `luma_kv_encode_f32` / `luma_kv_decode_f32` 函数体；保持 ABI；更新头注释去掉「恒等」表述 | `enc_len` 可 `< n`（或等价更密表示）；仍禁止未过三级门称「无损」 |
| A1.3 | 扩展 `tests/c/test_luma_kv.c`：空/极值长度/未对齐缓冲/非有限/容量不足/大 n（≥1e6 抽样） | ctest 全绿；L5：≥99.9% 元素过 2-ulp vs `luma_kv_ref_copy_f64`，直方图归档 |
| A1.4 | Python `@given` 覆盖 shape/dtype/有限性（`HYPOTHESIS_PROFILE=ha` 夜间） | `product/` 下至少 1 个 stateful 或高例属性测试绿 |

### F-A2 接口与算子文档生效

| 步骤 | 措施 | 验收 |
|---|---|---|
| A2.1 | 写满 `LUM-ARC-301`：缓冲所有权、重叠禁令、错误码域、GIL/线程、版本兼容 | 绑定实现可逐条对照；无「待撰写」 |
| A2.2 | `LUM-ARC-201` 含 FLOP/峰值字节公式，供 L4 与 Phase-1 实验共用 | L4 工作负载引用同一公式 ID |

### F-A3 Scheduler / 可选核插拔（不破坏物理三层）

| 步骤 | 措施 | 验收 |
|---|---|---|
| A3.1 | 新增物理目录 **`lumina/runtime/`**（Scheduler 落位；需 **迁移单 + ARC-101 补丁**，禁止塞进 `algorithm/`） | 仅编排；零算子数学；依赖只向下到 wrapper 公开 API |
| A3.2 | 可选脉冲 / 事件核：`kernel/optional/spike/`（或同等前缀），CMake `LUMINA_BUILD_SPIKE=OFF` | 默认关闭；主路径零符号依赖 |
| A3.3 | 混合注意力：先接口（Binding）后核；禁止 vendor `flash-attn` 作真源 | 基线可对比，产品核 `luma_*` |

### F-S1～S5 工程可信度

| ID | 措施 | 验收 |
|---|---|---|
| F-S1 | `workloads.py` 改为调用 `_luma_native` Enc/Dec（及可选 CUDA）；更新 `l4_perf_baseline.json` | 门禁失败当真实核回归；删除 saxpy 作为唯一分数 |
| F-S2 | `tests/python/product/test_kv_properties.py` 读 `[hypothesis]` | `make test-ci` + 文档化 `test-ha` |
| F-S3 | CI matrix：`LUMINA_BUILD_CUDA=ON` 可选 job；`tests/c` 或 pytest `@cuda` | 无 GPU 时显式 skip，非静默假绿 |
| F-S4 | `LUMA_ERR_CUDA` 迁至 `kernel/luma_cuda.h`（或 `luma_status_cuda.h`）；algorithm 枚举只保留通用码 | algorithm 头无 CUDA 字样；映射表更新 |
| F-S5 | 拆模块：`_luma_native`（仅产品）与 `_luma_baseline`（quant/SVD）；CUDA 同理 | `import` 路径文档化；README 明示基线非产品 |

### F-G* / F-R*

| ID | 措施 | 验收 |
|---|---|---|
| F-G1 | 启用 `[c_thresholds].max_cyclomatic_complexity=5`、`max_if_nesting=2`（见 target toml） | `native.gate` 实现并 FAIL 超标 |
| F-G2 | 根 README 上游体迁移 | 首页仅 Luminas 四平面 |
| F-G3 | 删除空 `kernel/test/`；`research/` 写最小协议索引；首个 `experiments/EXP-001/` | 无空壳；有一份 lab log 模板 |
| F-G4 | 全文检索替换旧模块名 | 零 `ci_quality_gate` / `c_quality_gate` 残留（除历史 changelog） |
| F-R1/R2 | Makefile 目标 `sanitize` / `tidy` | 文档进 ENG-301；可选 CI |

---

## 3. 目录重构方案（遵守物理三层冻结）

### 3.1 原则（不可破）

1. **不改** `algorithm/`、`kernel/`、`wrapper/` 路径语义；**不**引入与 CMake 冲突的 `src/lumina`。
2. 四平面导航保留；`theory/` **不**并入 `research/`。
3. 大挪移必须迁移单 / commit 粒度。
4. **不做** `tools/`→`scripts/` 第三轮改名。

### 3.2 目标目录树（标注职责与文件类型）

```text
lumina/
├── CMakeLists.txt              # 构建真值源（superproject）
├── Makefile / pyproject.toml / quality-gate.toml
├── README.md                   # 四平面 + Engineering 入口（无上游营销体）
│
├── algorithm/                  # Product · 纯 C 数学（.h/.c）
│   ├── luma_kv.h               # 产品 ABI（无 CUDA 错误码）
│   ├── luma_kv_codec.c         # 真 Enc/Dec（非恒等）
│   ├── luma_kv_finite.c / luma_kv_ref.c / luma_status.c
│   └── README.md
│
├── kernel/                     # Product · 硬件映射（.c/.cu/.h）
│   ├── baseline/               # 有损基线 ONLY（.c/.h）— 禁止产品叙事
│   ├── cuda/                   # CUDA 基线/加速（.cu）；符号带 baseline_ 前缀更佳
│   ├── optional/               # 可选插拔（默认 OFF）
│   │   └── spike/              # 脉冲/事件核（未来）
│   ├── luma_kernel.h / luma_cuda.h / luma_cuda_device.h
│   └── README.md               # 删除空 test/ 子目录
│
├── wrapper/                    # Product · Binding（.cpp）
│   ├── luma_bind_native.cpp    # 仅产品 API
│   ├── luma_bind_baseline.cpp  # 有损基线（新建拆分）
│   ├── luma_bind_cuda.cpp
│   └── README.md
│
├── runtime/                    # Scheduler 落位（.py）— 需 ARC-101 补丁后新增
│   ├── __init__.py
│   ├── infer.py / train.py     # 编排 only
│   └── README.md
│
├── tools/                      # Engineering · 可导入门禁包（保持）
│   ├── run_quality_gate.py / complexity_precommit.py
│   ├── checks/{architecture,native,reliability,naming,performance,python,comments}/
│   ├── reporting/ / support/
│   └── README.md
│
├── tests/                      # Engineering · 镜像 taxonomy
│   ├── c/                      # 产品 + 基线 ctest 源
│   ├── python/
│   │   ├── checks/ support/ product/ baselines/
│   │   └── conftest.py helpers.py
│   └── reports/                # 门禁产物（gitignore）
│
├── docs/                       # Knowledge · LUM-* 规范
├── theory/state-cache/         # Knowledge · F1–F7（非产品）
├── refs/                       # Knowledge · 文献/规格（含 UPSTREAM 说明可选）
├── research/                   # Research ops · 协议/lab 规范
└── experiments/                # Research ops · EXP-* 归档
    └── EXP-001_<slug>/         # lab log · hashes · 配置锁
```

### 3.3 明确不进架构叙事

`.venv/` `.cache/` `build/` `outputs/` `__pycache__/` — gitignore；README 表不列。

---

## 4. 质量标准落地文件

| 交付物 | 路径 | 用法 |
|---|---|---|
| L5 目标阈值 | [`../../quality-gate.l5-target.toml`](../../quality-gate.l5-target.toml) | Diff 审查后 **替换** `quality-gate.toml` |
| 命名 / 编码 | 仍以 `LUM-ENG-101` 为正文；本评审要求补：基线符号 `baseline` 段、C McCabe 与门禁对齐 | ENG-101 修订单另开 |
| 测试 | `LUM-ENG-301` 增补：`test-ha`、CUDA marker、L4 产品核、coverage 扩到 `algorithm` 绑定面 | 与本文件 §2 同步 |

**替换验收：**

1. `uv run python -m tools.run_quality_gate` 在存量代码上的预期：可能因新增 C 复杂度检查或 L4 工作负载变更而 **先红**——属预期，按 P0/P1 修到绿，禁止放宽阈值。
2. `ruff` / `complexity_precommit` 仍绿。
3. 头注释模块路径与 `tools.*` 一致，无旧名。

---

## 5. 架构优化说明

### 5.1 思路

```text
身份锁（arc） ──► 物理三层不变（eng） ──► 职责补齐靠「加目录/关可选」而非改冻结路径
       │
       ├── 产品真源：algorithm Enc/Dec + ARC-201/301
       ├── 基线隔离：kernel/baseline + 独立 pybind 模块
       ├── 编排外置：runtime/（Scheduler）只调公开 Binding
       └── 证明外置：experiments/EXP-* + res 三级门（非 eng 单测）
```

### 5.2 如何保障四性

| 目标 | 机制 |
|---|---|
| 分层清晰 | ARC-101 继续作唯一裁决；新增 `runtime/`/`optional/` 必须先改 101 |
| 源码隔离 | 上游只读；CI grep 禁 `from mamba` / `flash_attn` 进 `lumina/` 产品路径 |
| 高复用 | 有限性 / 错误串 / 设备工具已抽；禁止在 baseline 与 product 复制 2-ulp 逻辑——共享 `algorithm` 契约 |
| 可扩展 | 可选核 CMake OFF；开闭：新算法改 codec 或加 `kernel/optional/*`，不改 Binding 形状除非走 301 版本策略 |

### 5.3 与「超越一线大厂平均」的诚实映射

| 已具备（可宣称） | 尚未具备（不可宣称） |
|---|---|
| 物理分层 + 门禁 taxonomy + 双语报告 + 命名闸 | 工业级无损 KV 算子 |
| 非目标边界执行 | 混合注意力 / 脉冲主叙事对应实现 |
| 候选路径诚实注释 | 三级无损门归档 |

整改完成后，**工程规范性**可对标顶级开源组件；**产品能力**仍取决于 A1–A3 与 res 三级门，二者不可互相替代。

---

## 6. 整改优先级路线图

```text
P0（立即，阻塞对外表述）
  ├─ P0.1 叙事降级：README / 发行说明仅 candidate；拆基线导出（F-S5）
  ├─ P0.2 抽离 LUMA_ERR_CUDA（F-S4）
  ├─ P0.3 清空旧模块名注释（F-G4）；删 kernel/test/（F-G3 卫生）
  └─ P0.4 撰写 ARC-201/301 最小可生效正文（F-A2）← 可与公式选型并行草稿

P1（版本内 = M1 候选无损路径，见 LUM-PM-001）
  ├─ P1.1 真 Enc/Dec + C/Py L1/L5（F-A1）✅
  ├─ P1.2 Hypothesis 产品接线 + test-ha（F-S2）✅
  ├─ P1.3 L4 换产品核基线（F-S1）✅
  ├─ P1.4 CUDA 可选 CI + 测试（F-S3）✅ `run_build --cuda` · `@cuda` · `_luma_cuda`
  ├─ P1.5 C McCabe/嵌套门禁落地（F-G1 + target toml）✅ CC≤5 / if≤2（baseline/cuda 豁免）
  └─ P1.6 替换 quality-gate.toml ← quality-gate.l5-target.toml ✅（二者同步）

P2（长期 = M2+ 工业开源形态）
  ├─ P2.1 runtime/ Scheduler（F-A3.1）+ ARC-101 补丁
  ├─ P2.2 optional spike / hybrid（F-A3.2–3）
  ├─ P2.3 EXP-* + L2/L3 三级门归档（F-R4）
  ├─ P2.4 sanitizer / clang-tidy（F-R1/R2）
  └─ P2.5 根 README 上游体外置（F-G2/F-R5）
```

### 依赖关系

- **真 codec（P1.1）依赖** ARC-201 公式锁定（P0.4）。
- **L4 产品核（P1.3）依赖** P1.1 或至少可重复的 native 扩展构建。
- **论文级无损（算子重构）依赖** P1.1 + EXP-001 Level 1 归档 + `LUM-RES-001` §2.1 恒等条款；完整经验 L2/L3 表仍走 P2.3。
- **runtime/ 依赖** 稳定 Binding；勿与 P0 并行大挪移。

### 停止点（本评审明确不做）

- 不搬 `theory/`、不改 Product 三层目录名、不做 tools 第三轮改名、不以 GPTQ/AWQ/HQQ/剪枝/FlashAttention 充当产品路径、不以 F1–F7 通过宣称产品无损。

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 1.0 | 2026-09-05 | 首版全量评审交付；基准 `d3120b2` |
| 1.1 | 2026-09-05 | P1.4–P1.6 落地；EXP-001 L1 归档；论文级无损恒等条款对齐 RES-001 |
