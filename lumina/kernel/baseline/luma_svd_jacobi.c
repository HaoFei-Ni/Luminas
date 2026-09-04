/**
 * @file luma_svd_jacobi.c
 * @brief 对称 Jacobi 特征分解 + argsort（截断 SVD 私有）。
 *
 * 算法：经典 Jacobi（A ← JᵀAJ，V ← VJ）。收敛：off ≤ tol·(1+diag_ss)。
 */
#include "baseline/luma_svd.h"

#include <math.h>
#include <string.h>

/* 与历史基线对齐的 sweep 预算：过小则大维不收敛。 */
int luma_svd_jacobi_sweep_budget(int dim)
{
    int sweeps = dim * LUMA_JACOBI_SWEEP_SCALE;

    /* FLOOR 防止极小 dim 预算过短，SCALE 使大维有足够旋转轮次。 */
    if (sweeps < LUMA_JACOBI_SWEEP_FLOOR)
        sweeps = LUMA_JACOBI_SWEEP_FLOOR;
    return sweeps;
}

/** V 置单位阵：特征向量累积旋转的起点。 */
static void luma_svd_jacobi_init_identity(double *v, int n)
{
    int i;

    memset(v, 0, (size_t)n * (size_t)n * sizeof(double));
    for (i = 0; i < n; ++i)
        v[i * n + i] = 1.0;
}

/** 单行严格上三角能量：拆开双层循环以过门禁。 */
static double luma_svd_jacobi_row_offdiag(const double *a, int n, int p)
{
    int q;
    double off = 0.0;

    for (q = p + 1; q < n; ++q)
        off += a[p * n + q] * a[p * n + q];
    return off;
}

/** 收敛判据分子/分母：非对角平方和 vs 对角能量。 */
static void luma_svd_jacobi_offdiag_energy(const double *a, int n, double *off_out,
                                          double *diag_ss_out)
{
    int p;
    double off = 0.0;
    double diag_ss = 0.0;

    for (p = 0; p < n; ++p) {
        diag_ss += a[p * n + p] * a[p * n + p];
        off += luma_svd_jacobi_row_offdiag(a, n, p);
    }
    *off_out = off;
    *diag_ss_out = diag_ss;
}

/** 对称相似变换：必须一次做完 A←JᵀAJ；禁止「先列后行」的破坏性双乘。 */
static void luma_svd_jacobi_rotate_pair(double *a, double *v, int n, int p, int q)
{
    int i;
    /* 浮点漂移下 a_pq≠a_qp 时取平均，保持对称旋转输入。 */
    double apq = 0.5 * (a[p * n + q] + a[q * n + p]);
    double app, aqq, tau, t, c, s, npp, nqq;

    /* |apq| 过小：旋转角不稳定且收益可忽略，跳过防抖动。 */
    if (fabs(apq) < LUMA_JACOBI_ROTATE_EPS)
        return;

    app = a[p * n + p];
    aqq = a[q * n + q];
    /* τ=(aqq-app)/(2 apq)；t=sign(τ)/(|τ|+√(τ²+1)) 为稳定 tan(θ/2)，避免 θ→π/2 溢出。 */
    tau = (aqq - app) / (2.0 * apq);
    t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(tau * tau + 1.0));
    c = 1.0 / sqrt(t * t + 1.0);
    s = t * c;

    /* 非对角行/列同步更新：写两侧以维持对称存储。 */
    for (i = 0; i < n; ++i) {
        double aip, aiq, nip, niq;

        if (i == p || i == q)
            continue;
        aip = 0.5 * (a[i * n + p] + a[p * n + i]);
        aiq = 0.5 * (a[i * n + q] + a[q * n + i]);
        nip = c * aip - s * aiq;
        niq = s * aip + c * aiq;
        a[i * n + p] = a[p * n + i] = nip;
        a[i * n + q] = a[q * n + i] = niq;
    }

    /* 2×2 对角块闭式更新后强制 a_pq=0（相似变换目标）。 */
    npp = c * c * app - 2.0 * s * c * apq + s * s * aqq;
    nqq = s * s * app + 2.0 * s * c * apq + c * c * aqq;
    a[p * n + p] = npp;
    a[q * n + q] = nqq;
    a[p * n + q] = a[q * n + p] = 0.0;

    /* V ← V J：特征向量随同一 Givens 累积。 */
    for (i = 0; i < n; ++i) {
        double vip = v[i * n + p];
        double viq = v[i * n + q];

        v[i * n + p] = c * vip - s * viq;
        v[i * n + q] = s * vip + c * viq;
    }
}

/** 固定 p 扫 q>p：拆嵌套循环。 */
static void luma_svd_jacobi_sweep_row(double *a, double *v, int n, int p)
{
    int q;

    for (q = p + 1; q < n; ++q)
        luma_svd_jacobi_rotate_pair(a, v, n, p, q);
}

/** 一轮完整 Jacobi sweep。 */
static void luma_svd_jacobi_one_sweep(double *a, double *v, int n)
{
    int p;

    for (p = 0; p < n - 1; ++p)
        luma_svd_jacobi_sweep_row(a, v, n, p);
}

/* 破坏 a；特征向列写入 v，特征值写入 e；超预算仍发散则 NUMERIC。 */
int luma_svd_jacobi_sym_eig(double *a, int n, double *v, double *e, int max_sweeps)
{
    int p, sweep;
    double off, diag_ss;

    luma_svd_jacobi_init_identity(v, n);

    for (sweep = 0; sweep < max_sweeps; ++sweep) {
        luma_svd_jacobi_offdiag_energy(a, n, &off, &diag_ss);
        /* 相对能量门：+1 防止 diag_ss≈0 时误早停。 */
        if (off <= LUMA_JACOBI_CONVERGE_TOL * (1.0 + diag_ss))
            break;
        luma_svd_jacobi_one_sweep(a, v, n);
    }

    for (p = 0; p < n; ++p)
        e[p] = a[p * n + p];

    /* 预算耗尽仍大非对角 → 数值失败，禁止静默返回半收敛谱。 */
    if (sweep >= max_sweeps) {
        luma_svd_jacobi_offdiag_energy(a, n, &off, &diag_ss);
        if (off > LUMA_JACOBI_DIVERGE_TOL * (1.0 + diag_ss))
            return LUMA_ERR_NUMERIC;
    }
    return LUMA_OK;
}

/** 选择排序内层：dim 小（≤512），O(n²) 可接受。 */
static int luma_svd_argsort_find_best(const double *e, const int *idx, int start, int n)
{
    int j;
    int best = start;

    for (j = start + 1; j < n; ++j)
        if (e[idx[j]] > e[idx[best]])
            best = j;
    return best;
}

/* 特征值降序下标：截断 SVD 取最大 r 个分量。 */
void luma_svd_argsort_desc(const double *e, int n, int *idx)
{
    int i;

    for (i = 0; i < n; ++i)
        idx[i] = i;
    for (i = 0; i < n - 1; ++i) {
        int best = luma_svd_argsort_find_best(e, idx, i, n);

        if (best != i) {
            int tmp = idx[i];

            idx[i] = idx[best];
            idx[best] = tmp;
        }
    }
}
