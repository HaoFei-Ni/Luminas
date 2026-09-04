# lumina/algorithm — 纯算法层（规划中）

> 归属裁决：`../docs/arc/LUM-ARC-101`（当前为空目录，待冻结首批文件清单后迁移）。

## 应放入本目录的代码

- 平台无关、纯 ANSI C 的压缩/解压核心逻辑
- 无系统 API、无 CUDA 依赖、无副作用、无全局状态
- 编译期展开、运行时零循环/零递归（`eng-standard-skill` 最高优先级章节）

## 不应放入

- CUDA/平台专属算子 → `../kernel/`
- 对外 API / 绑定 / 内存与错误封装 → `../wrapper/`
- 有损基线对照 → `../kernel/baseline/`

## 参考规则

- 头文件仅接口声明，`.h` ≤ 300 行、`.c` ≤ 500 行、函数 ≤ 80 行（`eng-standard-skill`）
