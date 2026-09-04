# LUM-ARC-301 层间接口规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 计划 |
| 版本 | 0.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-arc-skill` · `lumina-eng-skill` |
| 关联文档 | `LUM-ARC-101` · `LUM-ENG-101` |

## 1. 范围（待撰写正文）

1. `algorithm` → `kernel` → `wrapper` 的调用边界与数据流契约。
2. `luma_*` / `luma_cuda_*` / `luma_triton_*` 符号级接口约定。
3. 每层头文件的最小接口原则与实现隐藏规则。
4. 内存所有权、128 字节对齐、错误码传播约定。

## 2. 约束

- 不在本文件重新定义分层（见 `LUM-ARC-101`）。
- 错误处理以 `lumina-eng-skill` 为准：公共 API 返回 `int` 错误码，不以 `errno` 报告错误。
