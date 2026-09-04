# LUM-ENG-201 构建系统与依赖管理规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 计划 |
| 版本 | 0.1 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-eng-skill`（Build） |
| 关联文档 | `LUM-ENG-001` · `LUM-ARC-101` |

## 1. 范围（待撰写正文）

1. CMake 目标划分（algorithm / kernel / wrapper / tools）；单一构建入口覆盖被测管线。
2. 编译器、CUDA toolkit、驱动族、Python 依赖锁定（`uv.lock`）；benchmark 报告须记录版本。
3. Conventional Commits：一提交一关注点；kernel 行为变更须附 L1 测试。

## 2. 现状指针

统一入口为 superproject：`lumina/CMakeLists.txt`。目标链：`luma_algorithm` → `luma_cpu` / `luma_cuda` → `_luma_native` / `_luma_baseline` / `_luma_cuda`。构建与测试命令见根 `README.md` 与 `lumina/tests/README.md`。
