# LUM-ENG-201 构建系统与依赖管理规范

| 字段 | 内容 |
|:---|:---|
| 状态 | 生效（最小正文） |
| 版本 | 0.2 |
| 日期 | 2026-09-05 |
| 权威技能 | `lumina-eng-skill`（Build） |
| 关联文档 | `LUM-ENG-001` · `LUM-ARC-101` · `CMakePresets.json` |

## 1. 范围

1. CMake 目标划分（`algorithm` / `kernel` / `wrapper`）；单一构建入口覆盖被测管线。
2. Windows 下 CMake / Ninja / MSVC 发现与 PATH 固化（禁止「本机有 cmake 但 agent PATH 没有」）。
3. Python 依赖锁定（`uv.lock`）；benchmark / 门禁报告记录工具版本。

## 2. 目标链

统一入口：`lumina/CMakeLists.txt`（superproject）。

`luma_algorithm` → `luma_cpu` / `luma_cuda` → `_luma_native` / `_luma_baseline` / `_luma_cuda`

预设：`lumina/CMakePresets.json`（`windows-ninja` / `windows-ninja-cuda`）。  
产物目录：`outputs/build/lumina/`（相对仓库根）。

## 3. Windows 工具链（真值源）

本机 VS 18 BuildTools 已验证路径：

| 工具 | 路径 |
|---|---|
| CMake | `D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe` |
| Ninja | `...\CMake\Ninja\ninja.exe` |
| vcvars | `...\VC\Auxiliary\Build\vcvarsall.bat` |

### 3.1 一次配置（推荐）

在仓库根 PowerShell：

```powershell
. .\lumina\scripts\dev-env.ps1 -PersistUserPath
```

- 当前会话：立刻把 CMake/Ninja 前置到 `PATH`，并设置 `LUMINA_CMAKE` / `LUMINA_NINJA` / `LUMINA_VCVARS`。
- `-PersistUserPath`：写入 **User PATH**，之后新开的终端 / Cursor agent 默认可直接找到 `cmake`。

### 3.2 构建命令（优先用仓库包装器）

```powershell
cd lumina
uv run python -m tools.run_build --test
```

包装器会：发现 CMake/Ninja →（若无 `cl`）经 `vcvarsall x64` 注入 MSVC → `cmake --preset windows-ninja` → build → 可选 ctest。

等价手动：

```powershell
. .\lumina\scripts\dev-env.ps1
cd lumina
cmake --preset windows-ninja
cmake --build ..\outputs\build\lumina
ctest --test-dir ..\outputs\build\lumina --output-on-failure
```

### 3.3 Agent 约定（强制）

1. **禁止**在未加载 `dev-env` / `tools.support.dev_env` 的情况下断言「本机无 cmake」。
2. 调用顺序：`dev_env.prepend_tool_bins_to_path()` 或 `. .\lumina\scripts\dev-env.ps1`，再跑 cmake。
3. Python 侧发现逻辑：`tools/support/dev_env.py`（`find_cmake` / `find_ninja`）。

## 4. 依赖锁定

- Python 工具链：`pyproject.toml` + `uv.lock`。
- 原生扩展：由 CMake + 系统编译器构建；`pytest` 在缺扩展时对 `@native` / `@cuda` **skip**，不假绿。

## 5. 提交约定（摘要）

Conventional Commits；kernel / ABI 行为变更须附 L1 测试（见 `LUM-ENG-301`）。
