"""verify-degeneration.py — 深度神经网络表征坍缩统一理论 数值核验器（纯标准库，固定种子）。

三级串联对象（与 ../framework.tex 一一对应）：
  L0  精确秩亏判定（谱隙判决定律，Weyl/Mirsky 扰动界）
  L1  深度线性表示坍缩（Sylvester 秩界 + 瓶颈饱和 + ReLU 秩增反例边界）
  L2  核范数训练收缩（SVT 软阈值闭合解 + 0 级退化临界时间闭合公式）

可证伪判据（方向/阈值见各函数头注释）：
  F1 谱隙判决：‖E‖₂ < γ/2 ⇒ 阈值法精确恢复秩 r；‖E‖₂ ≥ γ 存在秩降扰动
  F2 Eckart–Young–Mirsky：rank≤k 最优残差 ‖A−A_k‖_F² = Σ_{i>k} σᵢ²
  F3 Weyl/Mirsky：|σᵢ(A+E)−σᵢ(A)| ≤ ‖E‖₂，且 ℓ₂ 逐点差 ≤ ‖E‖_F
  F4 Sylvester 秩界：rank(XW) ≤ min(rank X, rank W)
  F5 ReLU 秩增反例：rank 1 → rank 2（非线性可增秩，坍缩定律适用边界）
  F6 SVT 软阈值：U·max(Σ−λI,0)·Vᵀ 与闭式 rank=#{σᵢ>λ}、谱值一致
  F7 退化临界时间：核范数流 σᵢ(t)=max(σᵢ(0)−λt,0)，Tᵢ=σᵢ(0)/λ，rank(t)=#{σᵢ(0)>λt}

用法：
  python verify-degeneration.py                # E 层小规模精确算例（默认，秒级）
  python verify-degeneration.py --mc           # 蒙特卡洛大样本证伪（自落盘 txt）
  python verify-degeneration.py --data X       # 真实矩阵 JSON 数据入口
  python verify-degeneration.py --print-template
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from typing import TextIO, cast

SEED = 20240904
RANK_TOL_REL = 1e-12  # 数值秩相对容差（单侧 Jacobi 满相对精度 ~ε·σ₁）
DENSE_DIM_LIMIT = 128  # 真实数据离线稠密交接上限
MC_RESULT_FILE = "verify-degeneration-mc-results.txt"
REAL_RESULT_FILE = "verify-degeneration-real-results.txt"


# =====================================================================
# 线性代数内核（纯标准库）
# =====================================================================


def mat_T(a: list[list[float]]) -> list[list[float]]:
    """矩阵转置。"""
    return [list(col) for col in zip(*a)]


def mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """矩阵乘法（a: m×k, b: k×n -> m×n）。"""
    m, k, n = len(a), len(b), len(b[0])
    return [[sum(a[i][t] * b[t][j] for t in range(k)) for j in range(n)] for i in range(m)]


def frob(a: list[list[float]]) -> float:
    """Frobenius 范数。"""
    return math.sqrt(sum(x * x for row in a for x in row))


def svd(a: list[list[float]]) -> tuple[list[list[float]], list[float], list[list[float]]]:
    """精简 SVD：A = U · diag(σ) · Vᵀ，返回 (U[m×p], σ[p] 降序, Vt[p×n])，p=min(m,n)。

    采用单侧 Jacobi（列正交化），奇异值具有**满相对精度**（误差 ~ε·σ₁，
    不平方条件数），适用于小规模矩阵的精确秩 / 谱扰动核验。
    """
    m, n = len(a), len(a[0])
    if m >= n:
        return _svd_tall(a, m, n)
    # m < n：对 Aᵀ（n×m，行多列少）做长侧分解后换回 U/Vt
    bu, sigma, bvt = _svd_tall(mat_T(a), n, m)
    return mat_T(bvt), sigma, mat_T(bu)


def _svd_tall(a: list[list[float]], m: int, n: int) -> tuple[list[list[float]], list[float], list[list[float]]]:
    """单侧 Jacobi（前提 m≥n）：正交化 n 个列向量。

    返回 (U[m×n] 正交列, σ[n] 降序, Vt[n×n])。
    """
    b = [list(r) for r in a]  # m×n 工作阵
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(100):
        if _jacobi_sweep(b, v, m, n) < 1e-14:
            break
    sigma = [math.sqrt(sum(b[i][j] * b[i][j] for i in range(m))) for j in range(n)]
    u = [[(b[i][j] / sigma[j]) if sigma[j] > 1e-300 else 0.0 for j in range(n)] for i in range(m)]
    order = sorted(range(n), key=lambda j: -sigma[j])
    sigma_sorted = [sigma[j] for j in order]
    u_sorted = [[u[i][j] for j in order] for i in range(m)]
    v_sorted = [[v[i][j] for j in order] for i in range(n)]
    return u_sorted, sigma_sorted, mat_T(v_sorted)


def _jacobi_sweep(b: list[list[float]], v: list[list[float]], m: int, n: int) -> float:
    """一轮单侧 Jacobi 扫掠：对所有列对执行正交化，返回最大归一化内积（收敛判据）。"""
    off = 0.0
    for p in range(n):
        for q in range(p + 1, n):
            alpha = _col_dot(b, p, p, m)
            beta = _col_dot(b, q, q, m)
            gamma = _col_dot(b, p, q, m)
            denom = math.sqrt(alpha * beta)
            if denom < 1e-300:
                continue
            off = max(off, abs(gamma) / denom)
            if abs(gamma) / denom >= 1e-15:
                _rotate_pair(b, v, p, q, m, n, alpha, beta, gamma)
    return off


def _col_dot(b: list[list[float]], p: int, q: int, m: int) -> float:
    """第 p、q 列内积（含 p=q 时的自内积）。"""
    return sum(b[i][p] * b[i][q] for i in range(m))


def _rotate_pair(
    b: list[list[float]], v: list[list[float]], p: int, q: int, m: int, n: int, alpha: float, beta: float, gamma: float
) -> None:
    """对列对 (p,q) 施加消除 gamma 的 Jacobi 旋转，并同步累积右奇异向量。"""
    zeta = (beta - alpha) / (2.0 * gamma)
    t = math.copysign(1.0, zeta) / (abs(zeta) + math.sqrt(zeta * zeta + 1.0))
    c = 1.0 / math.sqrt(t * t + 1.0)
    s = c * t
    for i in range(m):
        bip, biq = b[i][p], b[i][q]
        b[i][p] = c * bip - s * biq
        b[i][q] = s * bip + c * biq
    for i in range(n):
        vip, viq = v[i][p], v[i][q]
        v[i][p] = c * vip - s * viq
        v[i][q] = s * vip + c * viq


def reconstruct(u: list[list[float]], s: list[float], vt: list[list[float]]) -> list[list[float]]:
    """U·diag(s)·Vᵀ（s 为任意谱缩放）。"""
    us = [[u[i][j] * s[j] for j in range(len(s))] for i in range(len(u))]
    return mat_mul(us, vt)


def svd_vals(a: list[list[float]]) -> list[float]:
    """降序奇异值。"""
    _, sigma, _ = svd(a)
    return sigma


def spec_norm(a: list[list[float]]) -> float:
    """谱范数 ‖A‖₂ = σ_max。"""
    sigma = svd_vals(a)
    return sigma[0] if sigma else 0.0


def rank(a: list[list[float]], tol_rel: float = RANK_TOL_REL) -> int:
    """数值秩（0 级退化语义：σᵢ > tol_rel·σ₁ 计数，相对容差）。"""
    sigma = svd_vals(a)
    if not sigma:
        return 0
    thresh = tol_rel * sigma[0]
    return sum(1 for s in sigma if s > thresh)


def relu(a: list[list[float]]) -> list[list[float]]:
    """逐元素 ReLU。"""
    return [[max(0.0, x) for x in row] for row in a]


def svt(a: list[list[float]], lam: float) -> list[list[float]]:
    """核范数软阈值收缩 U·max(Σ−λI,0)·Vᵀ（闭合解）。"""
    u, sigma, vt = svd(a)
    return reconstruct(u, [max(0.0, x - lam) for x in sigma], vt)


def truncate(a: list[list[float]], k: int) -> list[list[float]]:
    """硬阈值秩-k 截断（Eckart–Young 最优逼近）。"""
    u, sigma, vt = svd(a)
    s = sigma[:k] + [0.0] * (len(sigma) - k)
    return reconstruct(u, s, vt)


def diag_matrix(vals: list[float]) -> list[list[float]]:
    """对角矩阵（vals 依序放对角线）。"""
    n = len(vals)
    return [[vals[j] if i == j else 0.0 for j in range(n)] for i in range(n)]


def _emit(msg: str, fh: TextIO) -> None:
    """打印并落盘（可审计）。"""
    print(msg)
    fh.write(msg + "\n")


# =====================================================================
# F1  谱隙判决（Level 0 精确秩亏判定）
# =====================================================================


def _f1_exact(fh: TextIO) -> bool:
    """A=diag(3,2,1,0,0)：r=3, 谱隙 γ=1。扰动 E=δI 使 ‖E‖₂=δ<γ/2。

    验证：阈值 τ*=(δ+(γ−δ))/2=γ/2 处 #(σ̂≥τ*) = r 恒成立；
    与 δ≥γ 时秩降反例（减去 γ 于第三对角）。
    """
    base = [3.0, 2.0, 1.0, 0.0, 0.0]
    r, gamma = 3, 1.0
    ok = True
    for delta in (0.1, 0.3, 0.49):
        a_hat = diag_matrix([base[i] + delta for i in range(5)])  # E=δI，‖E‖₂=δ
        sig = svd_vals(a_hat)
        tau = (delta + (gamma - delta)) / 2.0
        got = sum(1 for s in sig if s >= tau)
        cond = delta < gamma / 2.0 and got == r
        _emit(f"  [F1] δ={delta:.2f} (γ/2=0.50) τ*={tau:.3f} 判定秩={got} (期望 {r}) -> {'OK' if cond else 'FAIL'}", fh)
        ok = ok and cond
    drop = diag_matrix([3.0, 2.0, 0.0, 0.0, 0.0])  # 第三对角 −γ
    got_drop = rank(drop)
    _emit(
        f"  [F1] 反例 δ=γ 裂解：谱={svd_vals(drop)} 秩={got_drop} (期望 {r - 1}) "
        f"-> {'OK' if got_drop == r - 1 else 'FAIL'}",
        fh,
    )
    return ok and got_drop == r - 1


def _f1_mc(fh: TextIO, rng: random.Random) -> tuple[int, int]:
    """随机对角谱 + δI 扰动，统计阈值法判定正确率（期望 100%）。"""
    n_trial = 5000
    correct = 0
    for _ in range(n_trial):
        r = rng.randint(1, 6)
        pos = sorted((rng.uniform(1.0, 5.0) for _ in range(r)), reverse=True)
        gamma = pos[-1]
        full = pos + [0.0] * (8 - r)
        delta = rng.uniform(0.0, gamma / 2.0)
        tau = (delta + (gamma - delta)) / 2.0
        a_hat = diag_matrix([x + delta for x in full])
        got = sum(1 for s in svd_vals(a_hat) if s >= tau)
        if got == r:
            correct += 1
    _emit(f"  [F1-MC] {n_trial} 次随机谱隙判决：正确 {correct}/{n_trial} (比例 {correct / n_trial:.4f})", fh)
    return n_trial, correct


# =====================================================================
# F2  Eckart–Young–Mirsky 低秩压缩
# =====================================================================


def _f2_one(a: list[list[float]], k: int) -> float:
    """残差 ‖A−A_k‖_F² 与闭式尾谱 Σ_{i≥k}σᵢ² 的绝对偏差。"""
    sigma = svd_vals(a)
    tail = sum(s * s for s in sigma[k:])
    resid = frob(_sub(a, truncate(a, k))) ** 2
    return abs(resid - tail)


def _sub(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _f2_exact(fh: TextIO) -> bool:
    a = diag_matrix([5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 0.0])
    ok = True
    for k in (1, 3, 5):
        err = _f2_one(a, k)
        ok = ok and err < 1e-9
        _emit(f"  [F2] diag(5,4,3,2,1,0,0) k={k} 残差 vs Σσ² 偏差={err:.2e} -> {'OK' if err < 1e-9 else 'FAIL'}", fh)
    return ok


def _f2_mc(fh: TextIO, rng: random.Random) -> tuple[int, float]:
    n_trial = 800
    worst = 0.0
    for _ in range(n_trial):
        m, n = rng.randint(3, 9), rng.randint(3, 9)
        a = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(m)]
        k = rng.randint(0, min(m, n))
        worst = max(worst, _f2_one(a, k))
    _emit(f"  [F2-MC] {n_trial} 组随机矩阵：最大 |残差−尾谱| = {worst:.2e} (须 <1e-8)", fh)
    return n_trial, worst


# =====================================================================
# F3  Weyl / Mirsky 奇异值扰动界
# =====================================================================


def _f3_check(fh: TextIO, rng: random.Random) -> tuple[int, float, float, int]:
    n_trial = 1500
    worst_weyl = float("-inf")
    worst_mirsky = float("-inf")
    viol = 0
    for _ in range(n_trial):
        m, n = rng.randint(3, 8), rng.randint(3, 8)
        a = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(m)]
        e = [[rng.gauss(0.0, 0.5) for _ in range(n)] for _ in range(m)]
        a_hat = _add(a, e)
        sig_a = svd_vals(a)
        sig_ah = svd_vals(a_hat)
        en, ef = spec_norm(e), frob(e)
        worst_weyl = max(worst_weyl, max(abs(sig_ah[i] - sig_a[i]) - en for i in range(len(sig_a))))
        l2 = math.sqrt(sum((sig_ah[i] - sig_a[i]) ** 2 for i in range(len(sig_a))))
        worst_mirsky = max(worst_mirsky, l2 - ef)
        if l2 > ef + 1e-9:
            viol += 1
    _emit(
        f"  [F3] {n_trial} 组：Weyl 最大超额={worst_weyl:+.2e} (≤0)，"
        f"Mirsky 最大超额={worst_mirsky:+.2e} (≤0)，ℓ₂ 违例 {viol}",
        fh,
    )
    return n_trial, worst_weyl, worst_mirsky, viol


def _add(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


# =====================================================================
# F4  Sylvester 秩界 / 深度线性坍缩
# =====================================================================


def _f4_check(fh: TextIO, rng: random.Random) -> tuple[int, int]:
    n_trial = 1000
    viol = 0
    for _ in range(n_trial):
        m, k, n = rng.randint(3, 8), rng.randint(3, 8), rng.randint(3, 8)
        x = [[rng.gauss(0.0, 1.0) for _ in range(k)] for _ in range(m)]
        w = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(k)]
        if rank(mat_mul(x, w)) > min(rank(x), rank(w)):
            viol += 1
    _emit(f"  [F4] {n_trial} 组随机 X,W：rank(XW)≤min(rankX,rankW) 违例 {viol}", fh)
    return n_trial, viol


# =====================================================================
# F5  ReLU 秩增反例（非线性可增秩 -> 坍缩定律的适用边界）
# =====================================================================


def _f5_exact(fh: TextIO) -> bool:
    z = [[1.0, -1.0], [-1.0, 1.0]]  # 列互成负，rank 1
    r_before = rank(z)
    z_relu = relu(z)  # [[1,0],[0,1]] rank 2
    r_after = rank(z_relu)
    good = r_before == 1 and r_after == 2
    _emit(f"  [F5] ReLU 秩增：rank(Z)={r_before} -> rank(ReLU(Z))={r_after} -> {'OK' if good else 'FAIL'}", fh)
    return good


# =====================================================================
# F6  SVT 软阈值收缩闭合解
# =====================================================================


def _f6_check(fh: TextIO, rng: random.Random) -> tuple[int, int, float]:
    n_trial = 1000
    viol = 0
    worst = 0.0
    for _ in range(n_trial):
        vals = sorted((rng.uniform(0.1, 4.0) for _ in range(6)), reverse=True)
        lam = rng.uniform(0.1, 3.0)
        res = svt(diag_matrix(vals), lam)
        res_sigma = svd_vals(res)
        expect = sorted((max(0.0, v - lam) for v in vals), reverse=True)
        if rank(res) != sum(1 for v in vals if v > lam):
            viol += 1
        worst = max(worst, max(abs(res_sigma[i] - expect[i]) for i in range(6)))
    _emit(f"  [F6] {n_trial} 组对角谱：SVT 秩/谱闭合值 违例 {viol}，最大谱偏差={worst:.2e}", fh)
    return n_trial, viol, worst


# =====================================================================
# F7  退化临界时间闭合公式（核范数流 σ(t)=max(σ(0)−λt,0)）
# =====================================================================


def _f7_exact(fh: TextIO) -> bool:
    """核范数子梯度流 ṡ_i=−λ (s_i>0, 触 0 冻结) 的闭式 σ_i(t)=max(σ0_i−λt,0)。

    用独立 Euler 积分（细步长）与闭式解对比，验证退化临界时间 T_i=σ0_i/λ。
    """
    sig0 = [3.0, 2.0, 1.0, 0.5]
    lam = 0.75
    dt = 1e-4
    ok = True
    for t in (0.0, 0.5, 2.0, 5.0):
        steps = round(t / dt)
        sim = list(sig0)
        for _ in range(steps):
            sim = [s - lam * dt if s > 0.0 else 0.0 for s in sim]
        closed = [max(0.0, s - lam * t) for s in sig0]
        err = max(abs(sim[i] - closed[i]) for i in range(len(sig0)))
        good = err < 1e-6
        ok = ok and good
        _emit(
            f"  [F7] t={t:.1f}: Euler={[format(x, '.4f') for x in sim]} "
            f"闭式={[format(x, '.4f') for x in closed]} 最大偏差={err:.2e} "
            f"-> {'OK' if good else 'FAIL'}",
            fh,
        )
    t05 = 0.5 / lam
    _emit(f"  [F7] σ=0.5 的 0 级退化临界时间 T={t05:.6f}（=σ(0)/λ，闭式闭合）", fh)
    return ok


# =====================================================================
# E / MC 编排
# =====================================================================


def run_e(fh: TextIO) -> dict[str, bool]:
    _emit("=" * 72, fh)
    _emit("E 层（小规模精确算例）", fh)
    _emit("=" * 72, fh)
    rng = random.Random(SEED)
    _n3, weyl, mirsky, v3 = _f3_check(fh, rng)
    _n4, v4 = _f4_check(fh, rng)
    _n6, v6, _w6 = _f6_check(fh, rng)
    return {
        "F1": _f1_exact(fh),
        "F2": _f2_exact(fh),
        "F3": v3 == 0 and weyl <= 1e-9 and mirsky <= 1e-9,
        "F4": v4 == 0,
        "F5": _f5_exact(fh),
        "F6": v6 == 0,
        "F7": _f7_exact(fh),
    }


def run_mc(fh: TextIO) -> None:
    _emit("=" * 72, fh)
    _emit("蒙特卡洛证伪套件（--mc）", fh)
    _emit("=" * 72, fh)
    rng = random.Random(SEED)
    n1, c1 = _f1_mc(fh, rng)
    _n2, w2 = _f2_mc(fh, rng)
    _n3, weyl, mirsky, v3 = _f3_check(fh, rng)
    _n4, v4 = _f4_check(fh, rng)
    _n6, v6, w6 = _f6_check(fh, rng)
    _emit("", fh)
    _emit(
        f"  汇总: F1 {c1}/{n1} 正确 | F2 最大偏差 {w2:.2e} | "
        f"F3 Weyl {weyl:+.2e}/Mirsky {mirsky:+.2e}/违例 {v3} | "
        f"F4 违例 {v4} | F6 违例 {v6} 最大谱偏差 {w6:.2e}",
        fh,
    )


# =====================================================================
# --data 真实数据入口（JSON 契约 degeneration-v1）
# =====================================================================

DATA_TEMPLATE = {
    "format": "degeneration-v1",
    "source": {"name": "示例", "note": "离线矩阵交接（或仅谱）"},
    "records": [
        {
            "m": 4,
            "n": 4,
            "matrix": [[3.0, 0, 0, 0], [0, 2.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 0.0]],
            "truncation_ranks": [1, 2],
        }
    ],
}


def _validate_matrix(mat: object, where: str, m: int, n: int) -> list[list[float]]:
    if not isinstance(mat, list) or len(mat) != m:
        raise ValueError(f"{where}.matrix：必须为 m={m} 行")
    rows: list[list[float]] = []
    for i, row in enumerate(mat):
        if not isinstance(row, list) or len(row) != n:
            raise ValueError(f"{where}.matrix[{i}]：必须为 n={n} 列")
        for j, x in enumerate(row):
            if not isinstance(x, (int, float)) or not math.isfinite(float(x)):
                raise ValueError(f"{where}.matrix[{i}][{j}]：必须为有限数值")
        rows.append([float(x) for x in row])
    return rows


def load_real_data(path: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or data.get("format") != "degeneration-v1":
        raise ValueError("JSON：format 必须为 degeneration-v1")
    records = data.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("JSON：records 必须为非空数组")
    return cast("dict[str, object]", data), [_validate_record(rec, idx) for idx, rec in enumerate(records)]


def _validate_record(rec: object, idx: int) -> dict[str, object]:
    """单条记录契约校验（细化到字段路径）。"""
    if not isinstance(rec, dict):
        raise TypeError(f"records[{idx}]：必须为对象")
    m, n = _require_dims(rec, idx)
    mat = _validate_matrix(rec.get("matrix"), f"records[{idx}]", m, n)
    ranks = _require_ranks(rec, idx, m, n)
    name = _record_name(rec, idx)
    return {"m": m, "n": n, "matrix": mat, "ranks": ranks, "name": name}


def _require_dims(rec: dict[str, object], idx: int) -> tuple[int, int]:
    m, n = rec.get("m"), rec.get("n")
    if not isinstance(m, int) or not isinstance(n, int) or m < 1 or n < 1:
        raise ValueError(f"records[{idx}]：m,n 必须为正整数")
    return m, n


def _require_ranks(rec: dict[str, object], idx: int, m: int, n: int) -> list[int]:
    ranks = rec.get("truncation_ranks", [])
    if not isinstance(ranks, list) or not all(isinstance(r, int) and 0 <= r < min(m, n) for r in ranks):
        raise ValueError(f"records[{idx}].truncation_ranks：必须为 0<=r<min(m,n) 的整数数组")
    return cast("list[int]", ranks)


def _record_name(rec: dict[str, object], idx: int) -> str:
    src = rec.get("source")
    if isinstance(src, dict):
        nm = src.get("name")
        if nm is not None:
            return str(nm)
    return str(idx)


def run_real_data(path: str, fh: TextIO) -> None:
    _data, records = load_real_data(path)
    _emit("=" * 72, fh)
    _emit(f"真实数据核验（--data {path}）", fh)
    _emit("=" * 72, fh)
    for rec in records:
        mat = cast("list[list[float]]", rec["matrix"])
        m, n = cast("int", rec["m"]), cast("int", rec["n"])
        name = cast("str", rec["name"])
        if max(m, n) > DENSE_DIM_LIMIT:
            _emit(f"  {name}: {m}x{n} 超上限 {DENSE_DIM_LIMIT}，请走谱路径", fh)
            continue
        sigma = svd_vals(mat)
        r = rank(mat)
        gamma = sigma[r - 1] if r else 0.0
        tail = sum(s * s for s in sigma[r:])
        _emit(f"  {name} ({m}x{n}): 秩 r={r} 谱隙 γ={gamma:.6e} 0级退化数={len(sigma) - r} 尾谱 Σσ²={tail:.6e}", fh)
        for k in cast("list[int]", rec["ranks"]):
            _emit(f"    trunc={k}: 最优残差 Σσ²={sum(s * s for s in sigma[k:]):.6e}", fh)


def print_template(fh: TextIO) -> None:
    _emit("数据契约模板（degeneration-v1）:", fh)
    _emit(json.dumps(DATA_TEMPLATE, ensure_ascii=False, indent=2), fh)


# =====================================================================
# 主入口
# =====================================================================


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="0 级退化判定理论核验器")
    parser.add_argument("--mc", action="store_true", help="蒙特卡洛大样本证伪")
    parser.add_argument("--data", metavar="FILE", help="真实矩阵 JSON 数据")
    parser.add_argument("--print-template", action="store_true", help="输出数据契约模板")
    args = parser.parse_args(argv)

    if args.print_template:
        with open(REAL_RESULT_FILE, "w", encoding="utf-8") as fh:
            print_template(fh)
        print(f"结果落盘：{REAL_RESULT_FILE}")
        return 0

    if args.data:
        with open(REAL_RESULT_FILE, "w", encoding="utf-8") as fh:
            run_real_data(args.data, fh)
        print(f"结果落盘：{REAL_RESULT_FILE}")
        return 0

    if args.mc:
        with open(MC_RESULT_FILE, "w", encoding="utf-8") as fh:
            run_mc(fh)
        print(f"结果落盘：{MC_RESULT_FILE}")
        return 0

    with open(REAL_RESULT_FILE, "w", encoding="utf-8") as fh:
        res = run_e(fh)
        fails = [k for k, v in res.items() if not v]
        _emit("", fh)
        _emit("E 层结论：" + ("全部判据通过" if not fails else "FAIL: " + ",".join(fails)), fh)
    print(f"结果落盘：{REAL_RESULT_FILE}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
