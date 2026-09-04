# LUM-ENG-201 构建系统与依赖管理规范

- 状态：**计划（尚未撰写）**
- 关联：`LUM-ENG-001` · `eng-standard-skill`（"Build" 章节）· `LUM-ARC-101`（目录迁移须同步 CMake）

## 计划覆盖内容

- CMake 目标划分（kernel / bind / tools），单一构建入口构建被测管线
- 编译器 / CUDA toolkit / 驱动 / Python 依赖锁定（`uv.lock`），benchmark 报告记录版本
- Conventional Commits：一个提交一个关注点，kernel 行为变更随 L1 测试

## 现状指针

- 现有构建：`lumina/kernel/CMakeLists.txt`（`luma_cpu`/`luma_cuda` 静态库 + `luma_test_*` + pybind 模块，`LUMINA_BUILD_CUDA` 默认 OFF）。
