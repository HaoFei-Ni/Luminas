# experiments/ — 实验归档

只存可复现产物，不写标准。设计规范见 `../docs/res/`；协议与 lab log 见 `../research/`。

按 `EXP-YYYYMMDD-XXX/` 归档（XXX 自 001 起，同日多组递增）。大型产物不入 git 时，在 `manifest.md` 登记外部路径。

## 目录模板

```text
EXP-YYYYMMDD-XXX/
├── README.md          # 结论摘要 + lab log 指针 + 表格
├── manifest.yaml      # 机器可读复现元数据
├── configs/           # 锁定 hparams / 模型配置
├── results/           # 数值结果（csv / json / 图）
└── artifacts/         # 可选：权重 / 日志 / 失败 run
```

## manifest.yaml（对齐 `lumina-res-skill`）

```yaml
exp_id: EXP-YYYYMMDD-XXX
date: YYYY-MM-DD
phase: 1-operator | 2-model | 3-task | ablation | sota
commit: <git commit hash>
seeds: [0, 1, 2, 3, 4]
gpu:                                # 型号；tier: S|M|L（S=4GB, M=24GB, L=80GB）
driver: ; cuda: ; compiler: ; os:
python: ; torch: ; deps:            # 或 uv.lock hash
dataset: {name, version, split, hash}
hparams: {...}
```

## 规则

1. 开跑前锁定 lab log（`../research/`），跑完再归档。
2. 每张表 / 图绑定 manifest 中的 commit；保留失败 run。
3. 数字口径：mean ± std、n = 5；确定性 kernel bench 为 2 warmup + 5 timed。
4. 无损口径以 `../docs/res/LUM-RES-001` 为准（含 bit-exact 恒等条款）；禁止 “zero degradation” 等模糊口号。
