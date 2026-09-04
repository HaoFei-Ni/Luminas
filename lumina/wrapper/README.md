# lumina/wrapper — 平台封装层（规划中）

> 归属裁决：`../docs/arc/LUM-ARC-101`（当前为空目录，待冻结首批文件清单后迁移）。

## 应放入本目录的代码

- 对外统一 API：封装平台差异、内存管理、错误处理
- C-ABI / pybind11 绑定入口（marshal、dtype/shape 校验、GIL 释放）
- 内部实现对调用方透明；头文件只暴露最小必要接口

## 不应放入

- 任何数值算法本体（→ `../algorithm/` 或 `../kernel/`）
- Python 调度/编排（→ `../research/` 或调度模块）

## 参考规则

- pybind 绑定 `.cpp` 只做 marshal/校验/异常映射，释放 GIL（`eng-standard-skill`）
