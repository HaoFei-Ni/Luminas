# LUM-ARC-301 层间接口规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 生效（最小契约） |
| 版本 | 0.2 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-arc-skill` · `lumina-eng-skill` |
| 关联文档 | `LUM-ARC-101` · `LUM-ARC-201` · `LUM-ENG-101` |

## 1. 范围

规定 `algorithm` → `kernel` → `wrapper`（及未来 `runtime/` Scheduler）的调用边界、符号分区、内存所有权与错误码传播。分层定义仍以 `LUM-ARC-101` 为准。

## 2. 数据流与调用方向

```text
runtime/ (未来 Scheduler, Python)
        │  仅调公开 Binding
        ▼
wrapper/  _luma_native | _luma_baseline | _luma_cuda
        │  编组 / GIL / 异常映射；无数值
        ▼
kernel/   luma_cpu / luma_cuda     （有损基线 + 设备映射）
        │  可调用 algorithm 契约；禁止重实现产品 Enc/Dec 数学
        ▼
algorithm/  luma_kv_* / luma_status_*  （纯 C 数学 + 通用错误串）
```

禁止：`algorithm` include `kernel`/`wrapper`；产品 Binding 链入有损基线目标（已拆 `_luma_baseline`）。

## 3. 符号与模块分区

| 模块 | 符号前缀 | 物理落位 | 绑定扩展 |
|---|---|---|---|
| 产品 KV | `luma_kv_*` / `luma_strerror` | `algorithm/` | `_luma_native` |
| CPU 有损基线 | `luma_quant_*` / `luma_svd_*` | `kernel/baseline/` | `_luma_baseline` |
| CUDA 有损基线 | `luma_cuda_*` | `kernel/cuda/` | `_luma_cuda` |
| 未来 Triton | `luma_triton_*` | （待定，须迁徙单） | 待定 |

Python 导出名必须与 C ABI 一一对应（见 `LUM-ENG-101`）。

## 4. 头文件最小暴露

| 头 | 可声明 | 禁止 |
|---|---|---|
| `algorithm/luma_kv.h` | 通用错误枚举、产品 Enc/Dec、FP64 预言机、`luma_strerror` | CUDA/系统 API、基线算子、实现 |
| `kernel/luma_kernel.h` | CPU 基线声明 | 产品 Enc 实现细节 |
| `kernel/luma_cuda.h` | CUDA 启动器、`LUMA_ERR_CUDA`、设备相关上限 | 把 CUDA 错误枚举灌回 `luma_kv.h` |

实现一律在 `.c` / `.cu` / 绑定 `.cpp`。

## 5. 内存所有权与对齐

1. **调用方分配**全部输入/输出缓冲；库不做隐式扩容。
2. **禁止原地**：输入与输出指针不得重叠（产品 Enc/Dec 与基线均适用，除非某基线文档显式允许并测试覆盖）。
3. 热路径缓冲目标 **128 字节对齐**（eng-skill）；Binding 层对 numpy 要求 C-contiguous。
4. CUDA：设备指针由调用方持有；测试友好 Binding 的 H2D/D2H 不得被误认为生产路径合同。

## 6. 错误码传播

| 码 | 定义位置 | 含义 |
|---|---|---|
| `LUMA_OK` (0) | `luma_kv.h` | 成功 |
| `LUMA_ERR_ARG` (-1) | `luma_kv.h` | 空指针 / 非法维 / 非法超参 |
| `LUMA_ERR_NOMEM` (-2) | `luma_kv.h` | 分配失败 |
| `LUMA_ERR_NUMERIC` (-3) | `luma_kv.h` | 非有限 / 数值失败 |
| `LUMA_ERR_CUDA` (-4) | `luma_cuda.h` `#define` | 平台后端（launch/runtime） |
| `LUMA_ERR_UNSUPPORTED` (-5) | `luma_kv.h` | 超出实现上限 |

规则：

- 公共 C API 返回 `int` 错误码，**不**写 `errno`。
- Binding：`rc != LUMA_OK` → Python 异常；文案优先 `luma_strerror(rc)`（`-4` 映射为 `platform backend error`）。
- 不静默吞掉 CUDA API 失败；launch 后检查 `cudaGetLastError` / 同步错误并映射为 `LUMA_ERR_CUDA`。

## 7. 线程与 GIL

- 产品 / 基线长序列 Binding：**释放 GIL** 再进 C/CUDA。
- `algorithm` 无全局可变状态；可重入（调用方自备缓冲）。
- CUDA 流：由调用方传入；`0` 表示默认流（基线约定）。

## 8. 版本与兼容

- 现行产品 ABI 为 **candidate**：恒等 Enc/Dec；签名稳定，语义允许在 `LUM-ARC-201` 公式 ID 升级时收紧 `enc_len` 行为。
- 破坏性变更（改签名、改错误码数值槽）须：升 `LUM-ARC-301` 版本 + ENG 变更单 + 测试同步。
- 未过三级无损门的发行说明**禁止**使用「无损 / lossless」字样（`LUM-PM-001`）。

## 9. 约束

- 不在本文件重新定义分层（见 `LUM-ARC-101`）。
- Scheduler（`runtime/`）落地前须先修订 `LUM-ARC-101` 物理落位表。
