# LUM-ENG-301 测试体系与工具链规范

- 状态：**计划（尚未撰写）**
- 关联：`LUM-ENG-001` · `eng-standard-skill`（"Tests (summary)" + `references/test-matrix.md`）

## 计划覆盖内容

- L1–L5 各层测试的落地方式、覆盖率测量与门槛
- 工具链：pytest + xdist + Hypothesis / mypy + ruff / nsys / ncu / torch.profiler / compute-sanitizer / pytest-benchmark
- CI 命令约定与"工程测试不授予 lossless 论文声明"的边界

## 执行准绳

`eng-standard-skill/references/test-matrix.md` 是唯一执行细节来源，本文档只做入口与决策记录。
