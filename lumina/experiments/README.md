# experiments/ — 实验归档（只存产物，不写标准）

按 `EXP-YYYYMMDD-XXX/` 归档（XXX 从 001 起，同日多组递增）。
每组实验独立目录，含复现元数据与产物。

> 设计规范在 `../docs/res/`；协议与 lab log 在 `../research/`；本目录是"可复现归档产物"。
> 大型产物不入 git 的，登记 `manifest.md` 指向外部存储路径。

## 目录模板

```text
EXP-YYYYMMDD-XXX/
├── README.md          # 结论摘要 + 指向 lab log + 表格
├── manifest.yaml      # 机器可读复现元数据（见下）
├── configs/           # 锁定 hparams / 模型配置
├── results/           # 数值结果（csv/json/图）
└── artifacts/         # 可选：权重/日志/失败 run 保留
```

## manifest.yaml 字段（对齐 research-skill 复现披露）

```yaml
exp_id: EXP-YYYYMMDD-XXX
date: YYYY-MM-DD
phase: 1-operator | 2-model | 3-task | ablation | sota   # 选择
commit: <git commit hash>          # 绑定产物
seeds: [0, 1, 2, 3, 4]             # 固定 5 seeds
gpu:                                # 型号 / 显存 tier S|M|L
driver: ; cuda: ; compiler: ; os:
python: ; torch: ; deps:           # 或指向 uv.lock hash
dataset: {name, version, split, hash}
hparams: {...}
```

## 规则

1. 开跑前先锁 lab log（`../research/`），跑完再归档；**先记录后跑**。
2. 每张表/图绑定 manifest 中的 commit；保留失败 run。
3. 数字口径：mean ± std、n=5、2 warmup + 5 timed（确定性 kernel bench）。
4. 不归档未过三级门槛却写 "lossless" 的结论（`../docs/res/LUM-RES-001`）。
