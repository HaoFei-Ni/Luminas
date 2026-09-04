# lumina/ — Luminas 唯一内容区

源码、正式文档与实验归档均收纳于此。分层裁决：`docs/arc/LUM-ARC-101`。仓库导航：根目录 `README.md`。

| 目录 | 职责 | 状态 |
|---|---|---|
| `algorithm/` | 平台无关 ANSI C 压缩 / 解压数学 | 已启用 |
| `kernel/` | C-ABI 头、CUDA / CPU 算子、有损基线 | 已启用 |
| `wrapper/` | 对外 API / pybind 封装 | 已启用 |
| `tools/` | 质量门禁与指标层（非算子） | 已启用 |
| `theory/` | 表征坍缩统一理论（`state-cache/`：framework + F1–F7） | 已启用 |
| `research/` | 实验协议与 lab log | 规划中 |
| `tests/` | C（ctest）+ Python（pytest） | 已启用 |
| `docs/` | 正式文档（arc / eng / res / pm × LUM-*） | 草案 / 生效并存 |
| `refs/` | 外部参考文献与规范 | 骨架 |
| `experiments/` | 实验归档 `EXP-YYYYMMDD-XXX/` | 骨架 |

## 分层模型

| 视图 | 权威 | 内容 |
|---|---|---|
| 职责四层 | `lumina-arc-skill` | Kernel → Binding → Scheduler → Infra |
| 物理三层 | `lumina-eng-skill` | `algorithm/` → `kernel/` → `wrapper/` |

**归属口径以 `docs/arc/LUM-ARC-101` 为唯一裁决点。**

## 迁移记录（摘要）

Phase A/B/C（2026-09）已完成：算法 / 绑定迁出、头拆分、命名规范化、superproject 三层目标链。统一构建入口：`lumina/CMakeLists.txt`。细节见 `docs/arc/LUM-ARC-101`。
