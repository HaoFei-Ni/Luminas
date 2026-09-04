#!/usr/bin/env python3
"""
verify-kv-compression-baseline.py
复现 kv-cache-cla-compression.md §21 的数值算例：基线压缩比 C 与 SQNR 一致性核验
Reproduce §21 numeric results: baseline compression ratio C and SQNR consistency.

公式来源 / Source formulas (doc §5, §6, §20, §21):
    R_Q      = (1/d) * sum_m log2(B_m)          # RVQ 码率
    H_res    = log2(2 * e * b / Delta)          # 拉普拉斯残差离散熵近似
    r_total  = rho * (R_Q + H_res) + r_mask     # 每分量总码率
    C        = 16 / r_total                     # 相对 fp16 的压缩率
    eps      = Delta^2 / 12                     # 均匀量化噪声功率 (引理 0.8)
    SQNR     = 10*log10(P_signal / eps)         # 信号量化噪声比 (§19.2)

仅依赖标准库 / stdlib only (no numpy in this environment).
"""

import math
import random
from collections import Counter
from typing import TypedDict


class MonteCarloStats(TypedDict):
    """Monte Carlo 实测统计（对照理论值）"""

    mse: float
    mse_theory: float
    sig_pow: float
    sig_pow_theory: float
    sqnr_db: float
    h_emp: float
    h_exact: float
    h_approx: float
    n_symbols: int


# ----------------------------------------------------------------------
# 1. 解析计算 / Analytic computation
# ----------------------------------------------------------------------


def rvq_rate(d: int, M: int, B: int) -> float:
    """R_Q = (1/d) * M * log2(B)  (doc §5.3)"""
    return M * math.log2(B) / d


def residual_entropy(b: float, delta: float) -> float:
    """H_res = log2(2*e*b/delta)  (doc §6.2)"""
    return math.log2(2.0 * math.e * b / delta)


def total_rate(rho: float, r_q: float, h_res: float, r_mask: float) -> float:
    """r_total = rho*(R_Q + H_res) + r_mask  (doc §20.1)"""
    return rho * (r_q + h_res) + r_mask


def compression_ratio(r_total: float) -> float:
    """C = 16 / r_total  (doc §20.2, fp16 基线)"""
    return 16.0 / r_total


# ----------------------------------------------------------------------
# 2. Monte Carlo 仿真 / Monte Carlo simulation
# ----------------------------------------------------------------------


def sample_laplace(b: float, n: int, rng: random.Random) -> list[float]:
    """逆变换采样 Laplace(0, b): x = -b * sign(u) * ln(1 - 2|u|), u~U(-1/2,1/2)"""
    xs = []
    for _ in range(n):
        u = rng.random() - 0.5
        x = -b * math.copysign(math.log(1.0 - 2.0 * abs(u)), u) if u != 0.0 else 0.0
        xs.append(x)
    return xs


def exact_quantized_laplace_entropy(b: float, delta: float, k_max: int = 2000) -> float:
    """
    量化拉普拉斯符号的精确离散熵 (用于对照 §6.2 的连续近似):
      P_0 = 1 - exp(-delta/(2b))
      P_k = exp(-|k|*delta/b) * sinh(delta/(2b)) / 1 ... 逐项积分:
      P_k = 0.5 * (exp(-(|k|-0.5)*delta/b) - exp(-(|k|+0.5)*delta/b)),  k != 0
    """
    s = delta / b
    p0 = 1.0 - math.exp(-s / 2.0)
    H = -p0 * math.log2(p0)
    for k in range(1, k_max + 1):
        pk = 0.5 * (math.exp(-(k - 0.5) * s) - math.exp(-(k + 0.5) * s))
        if pk <= 0.0:
            break
        H -= 2.0 * pk * math.log2(pk)  # 双侧对称 ±k
    return H


def monte_carlo(b: float, delta: float, n: int, seed: int) -> MonteCarloStats:
    """对 Laplace(b) 残差做步长 delta 的均匀量化, 实测 MSE/SQNR/熵"""
    rng = random.Random(seed)
    xs = sample_laplace(b, n, rng)

    ks = [round(x / delta) for x in xs]  # 量化索引
    mse = sum((x - k * delta) ** 2 for x, k in zip(xs, ks, strict=True)) / n
    sig_pow = sum(x * x for x in xs) / n  # 实测信号功率 (理论 2b^2)

    counts = Counter(ks)
    h_emp = -sum((c / n) * math.log2(c / n) for c in counts.values())

    return {
        "mse": mse,
        "mse_theory": delta * delta / 12.0,  # 引理 0.8
        "sig_pow": sig_pow,
        "sig_pow_theory": 2.0 * b * b,  # Laplace 二阶矩
        "sqnr_db": 10.0 * math.log10(sig_pow / mse),
        "h_emp": h_emp,
        "h_exact": exact_quantized_laplace_entropy(b, delta),
        "h_approx": residual_entropy(b, delta),
        "n_symbols": len(counts),
    }


# ----------------------------------------------------------------------
# 3. 主流程 / Main
# ----------------------------------------------------------------------


def main() -> None:
    # doc §21.1 参数
    d, M, B = 128, 4, 256
    rho, r_mask = 0.3, 1.0
    delta = 0.002

    print("=" * 74)
    print("Part 1  解析压缩比 (doc §21.2-21.4)")
    print("=" * 74)
    header = f"{'case':<18}{'b':>6}{'R_Q':>7}{'H_res':>9}{'r_total':>9}{'C':>8}"
    print(header)
    print("-" * 74)
    cases = [("(a) concentrated", 0.01), ("baseline", 0.02), ("(b) diffuse", 0.05)]
    for name, b in cases:
        r_q = rvq_rate(d, M, B)
        h_r = residual_entropy(b, delta)
        r_t = total_rate(rho, r_q, h_r, r_mask)
        c = compression_ratio(r_t)
        print(f"{name:<18}{b:>6.2f}{r_q:>7.2f}{h_r:>9.4f}{r_t:>9.4f}{c:>7.2f}x")

    print()
    print("doc 预期: baseline C=5.71x, (a) C=6.39x, (b) C=5.00x")

    print()
    print("=" * 74)
    print("Part 2  Monte Carlo 核验 SQNR 与残差熵 (基线 b=0.02, delta=0.002)")
    print("=" * 74)
    n = 200_000
    r = monte_carlo(b=0.02, delta=delta, n=n, seed=20260904)

    print(f"samples N                 = {n}")
    print(f"signal power  measured    = {r['sig_pow']:.6e}   (theory 2b^2 = {r['sig_pow_theory']:.6e})")
    print(
        f"quant MSE     measured    = {r['mse']:.6e}   (theory d^2/12 = {r['mse_theory']:.6e}, "
        f"ratio = {r['mse'] / r['mse_theory']:.4f})"
    )
    print(f"SQNR          measured    = {r['sqnr_db']:.2f} dB")
    print(
        f"SQNR doc-convention       = {10 * math.log10(0.02**2 / r['mse_theory']):.2f} dB   "
        f"(doc §21.2 用 b^2 作信号功率, 预期 ≈30.8 dB)"
    )
    print(
        f"SQNR true-power           = {10 * math.log10(r['sig_pow_theory'] / r['mse_theory']):.2f} dB   "
        f"(用 2b^2, 预期 33.80 dB)"
    )
    print(f"SQNR 6.02 dB/bit law      = {6.02 * r['h_approx']:.2f} dB   (6.02 * H_res, §19.2)")
    print()
    print(f"residual entropy measured = {r['h_emp']:.4f} bit   (symbols = {r['n_symbols']})")
    print(f"residual entropy exact    = {r['h_exact']:.4f} bit   (量化拉普拉斯精确离散熵)")
    print(f"residual entropy approx   = {r['h_approx']:.4f} bit   (doc §6.2: log2(2eb/d))")

    # 用实测熵回代压缩率公式, 验证端到端一致性
    r_q = rvq_rate(d, M, B)
    c_emp = compression_ratio(total_rate(rho, r_q, r["h_emp"], r_mask))
    c_doc = compression_ratio(total_rate(rho, r_q, r["h_approx"], r_mask))
    print()
    print(f"C (empirical H_res)       = {c_emp:.2f}x   vs   C (doc formula) = {c_doc:.2f}x")

    print()
    print("=" * 74)
    print("Part 3  PASS/FAIL 判定 (容差: C ±1%, MSE ±10%, H ±0.05 bit)")
    print("=" * 74)
    checks = [
        ("baseline C == 5.71x", abs(c_doc / 5.7053 - 1.0) < 0.01),
        (
            "case (a) C == 6.39x",
            abs(compression_ratio(total_rate(rho, r_q, residual_entropy(0.01, delta), r_mask)) / 6.3888 - 1.0) < 0.01,
        ),
        (
            "case (b) C == 5.00x",
            abs(compression_ratio(total_rate(rho, r_q, residual_entropy(0.05, delta), r_mask)) / 4.9985 - 1.0) < 0.01,
        ),
        ("MSE ≈ delta^2/12", abs(r["mse"] / r["mse_theory"] - 1.0) < 0.10),
        ("H_emp ≈ H_approx", abs(r["h_emp"] - r["h_approx"]) < 0.05),
        ("SQNR doc ≈ 30.8 dB", abs(10 * math.log10(0.02**2 / r["mse_theory"]) - 30.79) < 0.05),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print()
    print("ALL PASS" if all(ok for _, ok in checks) else "SOME CHECKS FAILED")


if __name__ == "__main__":
    main()
