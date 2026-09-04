# LUM-ARC-301 层间接口规范

- 状态：**计划（尚未撰写）**
- 关联：`LUM-ARC-101`（分层裁决）· `LUM-ENG-101`（命名与符号规范）

## 计划覆盖内容

- algorithm → kernel → wrapper 的调用边界与数据流契约
- `luma_*` / `luma_cuda_*` / `luma_triton_*` 符号级接口约定
- 每层头文件的最小接口原则与实现隐藏规则
- 内存所有权、对齐（128B）、错误码传播约定

## 约束

- 不在本文件重新定义分层（见 LUM-ARC-101）。
- 错误处理以 `eng-standard-skill` 为准：公共 API 返回 `int` 错误码，不用 `errno` 报错。
