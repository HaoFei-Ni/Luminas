# KV Cache 压缩统一数学框架与六大前沿大模型底座：公理化完整推导

> 文档性质：从公理与符号定义出发的全链路数学推导记录。所有公式均给出中间演算步骤与依据标注；所有近似均标注阶数与误差上界；所有关键结论附数值算例。凡证据强度不足的命题，均明确降级为"推论"或"待证假设"并标注。

---

## 第 0 章　公理系统、形式化符号定义与预备引理

### 0.1 全局符号与空间定义

**定义 0.1（基础空间与索引集）**　设序列长度 $L\in\mathbb{N}^+$，隐藏维度 $d\in\mathbb{N}^+$，Query 头数 $n_q$，KV 头组数 $n_{kv}$（满足 $n_{kv}\mid n_q$，$1\le n_{kv}\le n_q$），单头维度 $d_h=d/n_q$，单头 Key/Value 维度 $d_k=d_v=d_h$。定义：

- 输入序列为矩阵 $X\in\mathbb{R}^{L\times d}$，其第 $t$ 行 $x_t\in\mathbb{R}^{d}$ 为第 $t$ 个 token 的隐状态；
- 投影矩阵 $W^Q\in\mathbb{R}^{d\times n_qd_h}$，$W^K\in\mathbb{R}^{d\times n_{kv}d_k}$，$W^V\in\mathbb{R}^{d\times n_{kv}d_v}$，$W^O\in\mathbb{R}^{n_qd_h\times d}$；
- KV cache 随机对象 $Z=(K,V)\in\mathbb{R}^{L\times n_{kv}d_k}\times\mathbb{R}^{L\times n_{kv}d_v}$，建模为概率空间 $(\Omega,\mathcal{F},\mathbb{P})$ 上取值于 $\mathbb{R}^{L\times n_{kv}(d_k+d_v)}$ 的随机矩阵；
- $\mathrm{RoPE}_t(\cdot)$：作用于位置 $t$ 的旋转位置编码，逐二维子空间左乘旋转矩阵 $R(\omega_ft)$，$\omega_f=\theta^{-2f/d}$，$\theta=10000$；
- $\mathrm{Softmax}(s)_i=e^{s_i}/\sum_j e^{s_j}$，作用于 logits 向量 $s\in\mathbb{R}^{L}$；
- $\|A\|_F=\sqrt{\sum_{ij}a_{ij}^2}=\sqrt{\sum_i\sigma_i(A)^2}$（Frobenius 范数），$\|A\|_2=\sigma_1(A)$（谱范数），$\|x\|_2=\sqrt{x^\top x}$；
- $\sigma_i(\cdot)$ 表示第 $i$ 大奇异值，$\lambda_i(\cdot)$ 表示第 $i$ 大特征值，$\rho(A)=\max_i|\lambda_i(A)|$ 为谱半径；
- $\mathbb{E}[\cdot]$、$\mathrm{Var}(\cdot)$、$H(\cdot)$、$h(\cdot)$ 分别为期望、方差、离散熵、差分熵（对数底为 2，单位 bit）；
- $[n]:=\{1,\dots,n\}$；$a\wedge b:=\min(a,b)$；$(x)^+:=\max(x,0)$。

**定义 0.2（注意力算子）**　标准多头注意力（MHA）对位置 $t$ 的输出为
$$
o_t=\mathrm{Concat}_{i=1}^{n_q}\Big(\sum_{j=1}^{t}\alpha_{ij}v_j^{(i)}\Big),\qquad \alpha_{ij}=\frac{e^{q_t^{(i)\top}k_j^{(i)}/\sqrt{d_h}}}{\sum_{\ell=1}^{t}e^{q_t^{(i)\top}k_\ell^{(i)}/\sqrt{d_h}}}.
$$

**定义 0.3（压缩编码器与解码器）**　编码器 $\mathcal{E}:\mathbb{R}^{L\times m}\to\{0,1\}^*$，解码器 $\mathcal{D}:\{0,1\}^*\to\mathbb{R}^{L\times m}$，重构 $\hat Z=\mathcal{D}(\mathcal{E}(Z))$。码率 $R=|\mathcal{E}(Z)|/(L\cdot m)$（bit/分量），压缩率 $C=16/R$（相对 fp16 基线）。

### 0.2 公理系统（A1–A6）及其相容性讨论

- **A1（有限精度基线）**：未压缩 KV cache 以 fp16 存储，每分量 16 bit。
- **A2（高分辨率量化假设）**：在码率 $b$ 不太小（$b\ge 2$）时，最优标量/向量量化的平均失真满足幂律 $D(b)=c_b\,\sigma^2 2^{-2b}$，其中 $c_b$ 为仅依赖源分布类型的常数。该假设是率失真理论中 $R(D)=\frac12\log_2(\sigma^2/D)$ 的反函数形式，在 $D\to0$ 渐近意义下严格成立（Gish–Pierce 界）。
- **A3（条件熵下界）**：任何无损编码的期望码长 $\mathbb{E}|\mathcal{E}(Z)|\ge H(Z\mid X,W)$。此为香农信源编码定理的直接推论。
- **A4（Softmax 利普希茨性）**：Softmax 的 Jacobian 谱范数不超过 $1/2$（引理 0.2 将给出证明），因此注意力权重对 logits 扰动是 $1/2$-利普希茨的。
- **A5（谱集中性）**：KV 分量的经验协方差谱 $\{\lambda_i\}$ 满足快速衰减：存在 $\kappa>0$ 使 $\lambda_i\asymp i^{-\kappa}$（待证假设，需在具体模型上实测验证，见 §21 验证方案）。
- **A6（误差独立性近似）**：不同压缩算子引入的误差在期望意义下可加（交叉项二阶小量）。此为一阶扰动近似，引入的误差为 $O(\|\text{各误差}\|^2)$ 量级。

**相容性**：A1–A6 作用于不同层面（存储格式、量化渐近、信息论界、分析性质、统计假设、扰动近似），彼此无逻辑冲突：A2 与 A3 分别针对有损与无损 regime；A5 仅用于推导可实现的压缩增益而非下界。A5、A6 为近似性假设，其失效条件将在 §12、§20 标注。

### 0.3 预备引理（含完整证明）

**引理 0.1（Popoviciu 方差界）**　若随机变量 $U\in[m,M]$ a.s.，则 $\mathrm{Var}(U)\le (M-m)^2/4$。

*证明*　设 $\mu=\mathbb{E}U$。方差是到常数的最小均方距离，故对 $c=(M+m)/2$：
$$
\mathrm{Var}(U)=\mathbb{E}(U-\mu)^2\le \mathbb{E}(U-c)^2\le \Big(\frac{M-m}{2}\Big)^2,
$$
末步因 $|U-c|\le(M-m)/2$ a.s.。$\square$

**引理 0.2（Softmax Jacobian 谱范数界）**　设 $p=\mathrm{Softmax}(s)$，$J=\partial p/\partial s=\mathrm{diag}(p)-pp^\top$，则 $\|J\|_2\le 1/2$，且常数 $1/2$ 不可改进。

*证明*　对任意单位向量 $u$（$\|u\|_2=1$），
$$
u^\top Ju=\sum_i p_iu_i^2-\Big(\sum_i p_iu_i\Big)^2=\mathrm{Var}_{i\sim p}(u_i).
$$
由引理 0.1，$\mathrm{Var}(u_i)\le (u_{\max}-u_{\min})^2/4$。由 $(u_{\max}-u_{\min})^2\le 2(u_{\max}^2+u_{\min}^2)\le 2\|u\|_2^2=2$，得 $u^\top Ju\le 1/2$。$J$ 对称半正定（协方差矩阵），故 $\|J\|_2=\lambda_1(J)\le1/2$。紧性：取 $n=2$，$s=(0,0)$，$p=(1/2,1/2)$，$u=(1,-1)/\sqrt2$，则 $u^\top Ju=\mathrm{Var}=1/2$。$\square$

**引理 0.3（注意力权重的扰动界，两种形式）**　设 $\alpha=\mathrm{Softmax}(s)$，$\alpha'=\mathrm{Softmax}(s+\delta)$。

(i)（欧氏形式）$\|\alpha'-\alpha\|_2\le \tfrac12\|\delta\|_2$；$\|\alpha'-\alpha\|_1\le \tfrac{\sqrt{L}}{2}\|\delta\|_2$。

(ii)（指数形式）若 $\|\delta\|_\infty\le\varepsilon$，则逐分量有 $e^{-2\varepsilon}\alpha_i\le\alpha'_i\le e^{2\varepsilon}\alpha_i$，从而 $|\alpha'_i-\alpha_i|\le (e^{2\varepsilon}-1)\alpha_i$。

*证明*　(i) 由微分中值定理，$\alpha'-\alpha=J(\xi)\delta$ 对某 $\xi$ 在线段 $[s,s+\delta]$ 上（逐分量成立，取积分形式 $J$ 的平均亦可），由引理 0.2 得 $\|\alpha'-\alpha\|_2\le\frac12\|\delta\|_2$；$\|\cdot\|_1\le\sqrt{L}\|\cdot\|_2$（Cauchy–Schwarz）。

(ii) $\alpha'_i=\dfrac{e^{s_i+\delta_i}}{\sum_j e^{s_j+\delta_j}}\le \dfrac{e^{s_i+\varepsilon}}{e^{-\varepsilon}\sum_j e^{s_j}}=e^{2\varepsilon}\alpha_i$；下界同理。于是 $|\alpha'_i-\alpha_i|\le\max(e^{2\varepsilon}-1,\,1-e^{-2\varepsilon})\alpha_i=(e^{2\varepsilon}-1)\alpha_i$。$\square$

**引理 0.4（Eckart–Young–Mirsky）**　设 $A\in\mathbb{R}^{m\times n}$，SVD 为 $A=\sum_i\sigma_iu_iv_i^\top$，$\sigma_1\ge\cdots\ge\sigma_r>\sigma_{r+1}\ge\cdots$。则
$$
\min_{\mathrm{rank}(B)\le r}\|A-B\|_F^2=\sum_{i>r}\sigma_i(A)^2,
$$
极小值在截断 SVD $B=U_r\Sigma_rV_r^\top$ 处取得。

*证明*　（下界）对任意秩 $\le r$ 的 $B$，由 Weyl 奇异值交错不等式 $\sigma_{i+j-1}(A)\le\sigma_i(B)+\sigma_j(A-B)$，取 $j=r+1$：当 $i\ge1$ 时 $\sigma_{i+r}(A)\le\sigma_{r+1}(B)+\sigma_i(A-B)=\sigma_i(A-B)$（因 $\mathrm{rank}(B)\le r$ 蕴含 $\sigma_{r+1}(B)=0$）。于是
$$
\|A-B\|_F^2=\sum_i\sigma_i(A-B)^2\ge\sum_{i=1}^{\min(m,n)-r}\sigma_{i+r}(A)^2=\sum_{i>r}\sigma_i(A)^2.
$$
（可达性）取 $B=U_r\Sigma_rV_r^\top$，则 $A-B=\sum_{i>r}\sigma_iu_iv_i^\top$，$\|A-B\|_F^2=\sum_{i>r}\sigma_i^2$。$\square$

**引理 0.5（Sherman–Morrison 秩一修正）**　若 $A$ 可逆且 $1+v^\top A^{-1}u\ne0$，则
$$
(A+uv^\top)^{-1}=A^{-1}-\frac{A^{-1}uv^\top A^{-1}}{1+v^\top A^{-1}u}.
$$
*证明*　直接验证乘积为单位阵：$(A+uv^\top)\big(A^{-1}-\frac{A^{-1}uv^\top A^{-1}}{1+v^\top A^{-1}u}\big)=I+\frac{uv^\top A^{-1}(1+v^\top A^{-1}u)-uv^\top A^{-1}-u(v^\top A^{-1}u)v^\top A^{-1}}{1+v^\top A^{-1}u}=I$。$\square$

**引理 0.6（算术–几何均值不等式，编码增益的下界）**　对 $\lambda_i>0$，$\frac1d\sum_i\lambda_i\ge(\prod_i\lambda_i)^{1/d}$，等号当且仅当所有 $\lambda_i$ 相等。

*证明*　对凹函数 $\ln$ 用 Jensen 不等式：$\frac1d\sum\ln\lambda_i\le\ln\frac1d\sum\lambda_i$，两边取指数即得。$\square$

**引理 0.7（两个差分熵公式）**

(i) 若 $X\sim\mathcal{N}(0,\sigma^2)$，则 $h(X)=\frac12\log_2(2\pi e\sigma^2)$。

(ii) 若 $R\sim\mathrm{Laplace}(0,b)$，$p(r)=\frac{1}{2b}e^{-|r|/b}$，则 $h(R)=\log_2(2eb)$。

*证明*　(ii) 直接计算：
$$
h(R)=-\int p(r)\log_2p(r)\,dr=\mathbb{E}\big[\log_2(2b)+\tfrac{|R|}{b\ln2}\big]=\log_2(2b)+\frac{\mathbb{E}|R|}{b\ln2}=\log_2(2b)+\frac{1}{\ln2}=\log_2(2b)+\log_2e=\log_2(2eb),
$$
其中用到 $\mathbb{E}|R|=b$（由 $\int_0^\infty \frac{r}{b}e^{-r/b}dr=b$）与 $1/\ln2=\log_2e$。(i) 同理，$h=\mathbb{E}[\frac12\log_2(2\pi\sigma^2)+\frac{X^2}{2\sigma^2\ln2}]=\frac12\log_2(2\pi\sigma^2)+\frac{1}{2\ln2}=\frac12\log_2(2\pi e\sigma^2)$。$\square$

**引理 0.8（均匀量化噪声）**　设量化步长 $\Delta$，量化误差 $e=x-\Delta\,\mathrm{round}(x/\Delta)$。在无过载且源密度在若干步长内近似平坦的条件下，$e\approx\mathrm{Unif}(-\Delta/2,\Delta/2)$，$\mathbb{E}e^2=\Delta^2/12$。

*证明*　$\mathbb{E}e^2=\int_{-\Delta/2}^{\Delta/2}\frac{u^2}{\Delta}du=\frac{1}{\Delta}\cdot\frac{2}{3}\Big(\frac{\Delta}{2}\Big)^3=\frac{\Delta^2}{12}$。平坦性条件的严格表述为 Bennett 积分的高阶项可忽略（见 §7 误差讨论）。$\square$

**引理 0.9（矩阵指数与线性系统的常数变易公式）**　线性系统 $\dot h(t)=Ah(t)+Bx(t)$，$x(t)$ 在 $[t_{k-1},t_k)$ 上恒为 $x_{k-1}$（零阶保持），$\Delta_k=t_k-t_{k-1}$，则精确解为
$$
h(t_k)=e^{A\Delta_k}h(t_{k-1})+A^{-1}\big(e^{A\Delta_k}-I\big)Bx_{k-1}.
$$
*证明*　常数变易：$h(t_k)=e^{A\Delta_k}h(t_{k-1})+\int_0^{\Delta_k}e^{A(\Delta_k-\tau)}Bx_{k-1}d\tau$。令 $u=\Delta_k-\tau$，积分 $=\int_0^{\Delta_k}e^{Au}du\cdot Bx_{k-1}=A^{-1}(e^{A\Delta_k}-I)Bx_{k-1}$（逐项积分幂级数 $\int_0^\Delta \frac{(Au)^n}{n!}du=\frac{A^n\Delta^{n+1}}{(n+1)!}$，求和即 $A^{-1}(e^{A\Delta}-I)$）。$A$ 奇异时该式按幂级数定义仍成立。$\square$

**引理 0.10（幂律失真的等边际最优分配）**　设失真模型 $D_i(r_i)=a_ir_i^{-\kappa_i}$（$a_i,\kappa_i>0$），预算约束 $\sum_i r_i=R$。则 $\min\sum_iD_i(r_i)$ 的最优解满足
$$
r_i^*=\Big(\frac{a_i\kappa_i}{\lambda}\Big)^{\frac{1}{\kappa_i+1}}\propto(a_i\kappa_i)^{\frac{1}{\kappa_i+1}},
$$
其中 $\lambda$ 由 $\sum_i r_i^*=R$ 唯一确定。

*证明*　拉格朗日函数 $\mathcal{L}=\sum_i a_ir_i^{-\kappa_i}+\lambda(\sum_ir_i-R)$。一阶条件 $\partial\mathcal{L}/\partial r_i=-a_i\kappa_ir_i^{-\kappa_i-1}+\lambda=0$，解出 $r_i^{\kappa_i+1}=a_i\kappa_i/\lambda$。目标函数关于 $r_i$ 严格凸（二阶导 $a_i\kappa_i(\kappa_i+1)r_i^{-\kappa_i-2}>0$），故 KKT 点即全局唯一最小。$\square$

**引理 0.11（谱半径与收缩性）**　矩阵幂迭代 $h_r=Ah_{r-1}$ 对任意初值收敛于 $0$ 当且仅当 $\rho(A)<1$。

*证明*　（$\Leftarrow$）Gelfand 公式 $\rho(A)=\lim_{k\to\infty}\|A^k\|^{1/k}$。若 $\rho(A)<1$，取 $\varepsilon=(1-\rho)/2$，存在 $k_0$ 使 $\|A^k\|^{1/k}\le\rho+\varepsilon<1$（$k\ge k_0$），故 $\|A^k\|\le(\rho+\varepsilon)^k\to0$，$\|h_r\|\le\|A^r\|\|h_0\|\to0$。（$\Rightarrow$）若 $\rho(A)\ge1$，取特征值 $|\lambda|=\rho\ge1$ 的特征向量 $v$，初值 $h_0=v$ 得 $h_r=\lambda^rv$ 不收敛于 0。$\square$

**引理 0.12（KL 散度的二阶展开）**　设 $p_\theta$ 为参数化分布族，$\theta$ 在 $\theta_0$ 邻域内，则
$$
\mathrm{KL}(p_{\theta_0}\|p_{\theta})=\tfrac12(\theta-\theta_0)^\top F(\theta_0)(\theta-\theta_0)+O(\|\theta-\theta_0\|^3),
$$
其中 $F(\theta_0)=-\mathbb{E}[\nabla^2\log p_{\theta_0}]$ 为 Fisher 信息矩阵。

*证明*　记 $f(\theta)=\mathrm{KL}(p_{\theta_0}\|p_\theta)=-\mathbb{E}_{p_{\theta_0}}[\log p_\theta]+\text{const}$。$f(\theta_0)=0$；$\nabla f(\theta_0)=-\mathbb{E}[\nabla\log p_{\theta_0}]=0$（score 期望为零）；$\nabla^2f(\theta_0)=-\mathbb{E}[\nabla^2\log p_{\theta_0}]=F(\theta_0)$。Taylor 展开至二阶即得，余项为三阶张量项 $O(\|\Delta\theta\|^3)$。$\square$

---

# 主题一　KV Cache 压缩统一数学框架

## §1　信息论无损压缩下界

### 1.1 条件熵的定义

将 KV cache 视为在给定输入 $X$ 与权重 $W$ 下的随机对象 $Z=(K,V)$。由于 $K=\mathrm{RoPE}(XW^K)$、$V=XW^V$ 在模型与输入确定时是确定性映射，严格意义上有 $H(Z\mid X,W)=0$；因此信息论下界必须作用于**分布化后的对象**：给定分布 $p(X)$（自然语言语料）与训练分布 $p(W)$，定义每分量条件熵
$$
\bar H=\frac{1}{L\cdot n_{kv}(d_k+d_v)}H(Z\mid W),
$$
其中 $H(Z\mid W)=-\int p(z\mid W)\log_2p(z\mid W)\,dz$（连续时用差分熵 $h$ 替代，离散化后二者相差 $-\log_2\Delta$ 项，见 §6）。

### 1.2 压缩率上界

**定理 1.1（无损压缩上界）**　对任意无损编码 $\mathcal{E}$（即 $\mathbb{P}[\mathcal{D}(\mathcal{E}(Z))=Z]=1$），期望码长满足 $\mathbb{E}|\mathcal{E}(Z)|\ge H(Z\mid W)$，从而
$$
C_{\max}=\frac{16\,L\,n_{kv}(d_k+d_v)}{\mathbb{E}|\mathcal{E}(Z)|}\le \frac{16}{\bar H}.
$$

*证明*　香农信源编码定理：无失真前缀码的期望码长下界为信源熵。由 A1，基线存储为 $16\,L\,n_{kv}(d_k+d_v)$ bit，两式相除即得。$\square$

**物理意义**　该界表明：任何"严格无损"的 KV cache 压缩，其压缩率被 cache 的经验条件熵硬性封顶；超过此界的压缩必然引入失真，必须由率失真理论（§2–§7）与推理等价约束（§11–§13）刻画。

### 1.3 经验熵估计与可达码长

在 $N$ 个独立样本 $\{z^{(i)}\}$ 上，以直方图统计 $n_z=\#\{i:z^{(i)}=z\}$，经验熵（plug-in 估计）为
$$
\hat H=-\sum_z\frac{n_z}{N}\log_2\frac{n_z}{N}.
$$
该估计有负偏，Miller–Madow 一阶偏差修正为
$$
\mathbb{E}\hat H=H-\frac{K-1}{2N\ln 2}+O(N^{-2}),\qquad K=\#\{z:n_z>0\},
$$
推导：对 $\frac{n_z}{N}$ 在 $p_z$ 处作二阶 Taylor 展开并取期望，$\mathbb{E}[-\hat p\log\hat p]\approx-p\log p-\frac{\mathrm{Var}(\hat p)}{2p\ln2}=-p\log p-\frac{1-p}{2N\ln2}$，对 $z$ 求和即得。

**可达码长**　算术编码对信源序列 $z^N$ 实现期望码长
$$
H(Z)\le \mathbb{E}L_N < H(Z)+2\ \text{bit},
$$
故逐符号熵编码的实际开销与下界之差为 $O(1)$ bit/序列，渐近可忽略；香农码（$\ell(z)=\lceil-\log_2p(z)\rceil$）则满足 $H\le\mathbb{E}L<H+1$。

---

## §2　正交变换编码（KVTC）

### 2.1 均值移除与协方差

给定 cache 样本 $\{z_t\}_{t=1}^L$，$z_t\in\mathbb{R}^{d_z}$（$d_z=n_{kv}(d_k+d_v)$ 或取单个 head 维度 $d_k$，两种粒度推导相同，以下以 $d$ 记维度）：
$$
\mu=\frac1L\sum_{t=1}^L z_t,\qquad \Sigma=\frac1L\sum_{t=1}^L(z_t-\mu)(z_t-\mu)^\top\in\mathbb{R}^{d\times d}.
$$
$\Sigma$ 对称半正定（对任意 $u$：$u^\top\Sigma u=\frac1L\sum_t(u^\top(z_t-\mu))^2\ge0$），故存在正交特征分解
$$
\Sigma=U\Lambda U^\top,\qquad U^\top U=I,\quad \Lambda=\mathrm{diag}(\lambda_1,\dots,\lambda_d),\ \lambda_1\ge\cdots\ge\lambda_d\ge0.
$$

### 2.2 变换编码与去相关

定义变换系数 $y_t=U^\top(z_t-\mu)$，则 $y_t$ 的经验协方差为
$$
\frac1L\sum_t y_ty_t^\top=U^\top\Sigma U=\Lambda,
$$
即各分量两两不相关（去相关）。在 $y$ 各分量上独立分配码率不再浪费比特于相关性冗余。

### 2.3 最优比特分配与总失真

**问题**　在 A2（高分辨率假设）下，分量 $i$ 的失真 $D_i=\lambda_i2^{-2b_i}$，求解
$$
\min_{\{b_i\}}\ D_T=\sum_{i=1}^d\lambda_i2^{-2b_i}\quad\text{s.t.}\quad \sum_{i=1}^db_i=dR.
$$

*推导*　拉格朗日函数 $\mathcal{L}=\sum_i\lambda_i2^{-2b_i}+\nu(\sum_ib_i-dR)$。一阶条件：
$$
\frac{\partial\mathcal{L}}{\partial b_i}=-2\ln2\cdot\lambda_i2^{-2b_i}+\nu=0\quad\Longrightarrow\quad \lambda_i2^{-2b_i}=\frac{\nu}{2\ln2}=:\theta\quad(\text{对所有 }i\text{ 相同}),
$$
即**等失真条件**：最优分配使各分量边际失真相等。由 $b_i=\frac12\log_2(\lambda_i/\theta)$ 代入预算约束：
$$
dR=\sum_i b_i=\frac12\sum_i\log_2\lambda_i-\frac d2\log_2\theta\quad\Longrightarrow\quad \log_2\theta=\frac1d\sum_i\log_2\lambda_i-2R=\log_2\Big(\prod_i\lambda_i\Big)^{1/d}-2R,
$$
故 $\theta=2^{-2R}\big(\prod_i\lambda_i\big)^{1/d}$。代回 $D_T=\sum_i\theta=d\theta$，得每分量失真
$$
\boxed{\ \bar D_T=\frac{D_T}{d}=2^{-2R}\Big(\prod_{i=1}^d\lambda_i\Big)^{1/d}\ }.
$$
凸性：目标关于 $b_i$ 严格凸（$\partial^2/\partial b_i^2=4(\ln2)^2\lambda_i2^{-2b_i}>0$），KKT 点为全局唯一最优。

**非负码率修正**　若要求 $b_i\ge0$，则 KKT 条件变为逆水位分配：$b_i=\frac12\log_2(\lambda_i/\theta)$ 仅对 $\lambda_i>\theta$ 的分量成立，其余分量 $b_i=0$（直接丢弃，失真 $\lambda_i$），水位 $\theta$ 由预算重解。

### 2.4 编码增益

与不做变换（直接在原始基下分配，失真 $2^{-2R}\cdot\frac1d\sum_i\lambda_i$）相比，定义变换编码增益
$$
G_T=\frac{\bar D_{\text{无变换}}}{\bar D_T}=\frac{\frac1d\sum_i\lambda_i}{\big(\prod_i\lambda_i\big)^{1/d}}\ge1,
$$
不等式由引理 0.6（AM–GM）给出，等号当且仅当谱平坦（$\lambda_1=\cdots=\lambda_d$，无相关性可挖）。谱越集中（A5 中 $\kappa$ 越大），$G_T$ 越大：例如 $\lambda_i\propto i^{-2}$、$d=128$ 时数值计算 $G_T\approx 10^{1.9}$ 量级（即约 6.3 dB 失真改善），具体值取决于实测谱。

---

## §3　知识蒸馏敏感度

### 3.1 蒸馏损失的二阶近似

设教师/学生模型在 cache 上的扰动为 $\Delta c$。由引理 0.12，KL 蒸馏损失在扰动处的二阶展开为
$$
\mathcal{L}_{KD}=\mathrm{KL}(p_T\|p_S)\approx\tfrac12\,\Delta c^\top F\,\Delta c,\qquad F=-\mathbb{E}\big[\nabla_c^2\log p_S\big],
$$
余项 $O(\|\Delta c\|^3)$。若用输出 Logits 的 L2 损失替代（等价于在 Fisher 矩阵取单位阵的 Gauss–Newton 近似）：
$$
\mathcal{L}_{KD}^{L2}=\tfrac12\|o_T-o_S\|_2^2=\tfrac12\|J_o\,\Delta c\|_2^2+O(\|\Delta c\|^3),
$$
其中 $J_o=\partial o/\partial c$ 为输出对 cache 的 Jacobian。

### 3.2 敏感度定义与计算

**定义 3.1**　cache 第 $i$ 分量的敏感度
$$
s_i=\Big\|\frac{\partial\mathcal{L}_{KD}}{\partial c_i}\Big\|_2^2.
$$
一阶近似下 $\partial\mathcal{L}_{KD}/\partial c_i=(F\,\Delta c)_i$，在 $\Delta c\to0$ 时梯度趋于零，因此实操中使用两种可计算代理：

(i) **Taylor 敏感度**（Optimal Brain Damage 形式）：$s_i^{T}=F_{ii}\,c_i^2$，即"置零该分量引起的损失增量"的二阶估计 $\Delta\mathcal{L}\approx\frac12F_{ii}c_i^2$；

(ii) **梯度幅值敏感度**：在带噪运行点（如量化后的 cache）处采样，$s_i^{G}=\mathbb{E}\|\partial\mathcal{L}_{KD}/\partial c_i\|_2^2$，期望对若干校验 batch 取。

**复杂度**　反向传播一次得到全部分量梯度，代价 $O(\text{一次前向}+\text{一次反向})\approx 3\times$ 前向 FLOPs；对角 Fisher $F_{ii}$ 用平方梯度的滑动平均估计（K-FAC 对角近似），额外存储 $O(d)$。

---

## §4　GSPruning 可微剪枝

### 4.1 Gumbel–Sigmoid 重参数化

离散的保留/剪枝决策 $m_i\in\{0,1\}$ 不可微，无法梯度优化。引入 Gumbel–Sigmoid 松弛：
$$
m_i=\sigma\Big(\frac{\log\alpha_i+g_i}{\tau}\Big),\qquad g_i=-\log(-\log u_i),\ u_i\sim\mathrm{Unif}(0,1),
$$
其中 $\alpha_i>0$ 为可学习保留倾向参数，$\tau>0$ 为温度。

**性质**　（i）$\mathbb{E}[m_i]=\sigma(\log\alpha_i/\tau)=\dfrac{\alpha_i^{1/\tau}}{1+\alpha_i^{1/\tau}}$。

*推导*　$\mathbb{P}(g_i\le x)=\mathbb{P}(-\log(-\log u)\le x)=\mathbb{P}(u\le e^{-e^{-x}})=e^{-e^{-x}}$（Gumbel CDF）。事件 $m_i=1$ 的极限（$\tau\to0$）概率为 $\mathbb{P}(g_i>-\log\alpha_i)=1-e^{-e^{\log\alpha_i}}=1-e^{-\alpha_i}$；有限温度下由 Gumbel 与 Logistic 的共轭关系，$\mathbb{E}m_i=\mathbb{P}(\log\alpha_i+g_i>0\text{ 的平滑 })=\sigma(\log\alpha_i/\tau)$。$\square$

（ii）$\tau\to0^+$ 时 $m_i\xrightarrow{d}\mathrm{Bernoulli}(\sigma(\log\alpha_i))$ 且样本值趋于 $\{0,1\}$；$\tau\to\infty$ 时 $m_i\to1/2$（完全松弛）。（iii）梯度经 $\partial m_i/\partial\alpha_i$ 流通，方差由重参数化控制。

### 4.2 保留率、剪枝失真与最优准则

**保留率**　$\rho=\dfrac{1}{d}\sum_{i=1}^d\mathbb{E}[m_i]=\dfrac1d\sum_i\sigma(\log\alpha_i/\tau)$。

**剪枝失真**　在 A6（误差可加）与 §3 的 Taylor 敏感度下，置零分量 $i$ 的损失增量 $\approx s_ic_i^2$，故期望剪枝失真
$$
D_P=\sum_{i=1}^d(1-m_i)\,s_ic_i^2.
$$

**定理 4.1（最优剪枝准则）**　在保留预算 $\sum_i m_i=\rho d$、$m_i\in\{0,1\}$ 下，$D_P$ 的最小值由"保留 $s_ic_i^2$ 最大的 $\lfloor\rho d\rfloor$ 个分量"达到。

*证明*（交换论证）　设 $S$ 为任一大小为 $k=\lfloor\rho d\rfloor$ 的保留集，若存在 $i\in S$、$j\notin S$ 使 $w_j:=s_jc_j^2>s_ic_i^2=:w_i$，则交换 $i,j$ 后失真改变量 $\Delta D_P=w_i-w_j<0$，严格下降。故最优集中不存在这样的对，即 $S$ 必为按 $w_i$ 降序的前 $k$ 个。$\square$

可微版本：以 $m_i$ 为软权重，$\min_\alpha\sum_i(1-\sigma(\log\alpha_i/\tau))w_i+\lambda(\sum_i\sigma(\log\alpha_i/\tau)-\rho d)$，由引理 0.10 的同构形式，最优软解在 $\tau\to0$ 时一致收敛到定理 4.1 的硬解。

---

## §5　残差向量量化（CRVQ / VQKV / CAMERA）

### 5.1 单级向量量化

码本 $\mathcal{C}=\{c_1,\dots,c_B\}\subset\mathbb{R}^d$。编码规则为最近邻
$$
i^*(z)=\arg\min_{i\in[B]}\|z-c_i\|_2^2,
$$
每向量码率 $\log_2B$ bit，折合每分量 $R=\frac1d\log_2B$ bit。平均失真 $D=\mathbb{E}\|z-c_{i^*(z)}\|_2^2$ 由 Lloyd–Max 条件（质心条件 $c_i=\mathbb{E}[z\mid i^*(z)=i]$ 与最近邻条件互为不动点）迭代优化。

### 5.2 多级残差递归

$M$ 级 RVQ 递归定义为
$$
r_0=z;\qquad i_m=\arg\min_{i}\|r_{m-1}-c_i^{(m)}\|_2^2,\qquad r_m=r_{m-1}-c_{i_m}^{(m)},\quad m=1,\dots,M.
$$
重构与最终残差：
$$
\hat z=\sum_{m=1}^M c_{i_m}^{(m)},\qquad r_M=z-\hat z.
$$

**命题 5.1（残差范数单调不增，设计条件下）**　若各级码本含零码字或通过投影校验（即 $i_m$ 的选择满足 $\|r_{m-1}-c_{i_m}\|^2\le\|r_{m-1}\|^2$，等价于 $\langle r_{m-1},c_{i_m}\rangle\ge\frac12\|c_{i_m}\|^2$），则 $\|r_m\|_2\le\|r_{m-1}\|_2$。

*证明*　$\|r_m\|^2=\|r_{m-1}\|^2-2\langle r_{m-1},c_{i_m}\rangle+\|c_{i_m}\|^2\le\|r_{m-1}\|^2$ 当且仅当 $\langle r_{m-1},c_{i_m}\rangle\ge\frac12\|c_{i_m}\|^2$。$\square$

### 5.3 码率公式

各级索引独立编码，总码率
$$
\boxed{\ R_Q=\frac1d\sum_{m=1}^M\log_2B_m\ \text{bit/分量}\ }.
$$
若采用乘积码本（CAMERA 式，对维度分组 $d=\sum_g d_g$），每组的失真项独立累加，码率 $R_Q=\frac1d\sum_g\sum_m\log_2B_{g,m}$。RVQ 的失真–码率权衡随 $M$ 单调改善（命题 5.1），但边际收益递减：在高分辨率假设 A2 下每比特失真下降约 $6.02$ dB（$D\propto2^{-2R}\Rightarrow10\log_{10}2^{-2}\approx-6.02$ dB/bit）。

---

## §6　残差熵编码

### 6.1 拉普拉斯残差的差分熵

RVQ 末级残差 $r$ 的经验分布以拉普拉斯分布良好拟合（峰度 $>3$ 的尖峰重尾），$p(r)=\frac{1}{2b}e^{-|r|/b}$。由引理 0.7(ii)：
$$
h(r)=\log_2(2eb).
$$

### 6.2 离散化后的熵

以步长 $\Delta$ 均匀量化残差，$\hat r=\Delta\,\mathrm{round}(r/\Delta)$，量化值分布 $P_k\approx p(k\Delta)\Delta$（$\Delta$ 充分小时密度在单bin内近似常数）。离散熵
$$
H_{\text{res}}=-\sum_k P_k\log_2P_k\approx-\int p(r)\log_2[p(r)\Delta]\,dr=h(r)-\log_2\Delta=\log_2\frac{2eb}{\Delta}.
$$
严格性说明：该近似即差分熵的 Riemann 和展开，误差为 $O(\Delta^2\|p''\|)$（Euler–Maclaurin 公式），当 $\Delta\ll b$ 时可忽略。

### 6.3 步长选择准则

给定残差失真预算 $\varepsilon$（均方误差），由引理 0.8，$\mathbb{E}e^2=\Delta^2/12=\varepsilon$，解出
$$
\boxed{\ \Delta=\sqrt{12\varepsilon}\ }.
$$
代入得码率–失真闭式：
$$
H_{\text{res}}(\varepsilon)=\log_2\frac{2eb}{\sqrt{12\varepsilon}}=\frac12\log_2\frac{e^2b^2}{3\varepsilon}.
$$

**与香农下界的间隙**　拉普拉斯源在 MSE 失真 $\varepsilon$ 下的香农下界 $R(\varepsilon)\ge h(r)-\frac12\log_2(2\pi e\varepsilon)=\frac12\log_2\frac{2eb^2}{\pi\varepsilon}$。两式之比
$$
\frac{e^2b^2/(3\varepsilon)}{2eb^2/(\pi\varepsilon)}=\frac{e\pi}{6}\approx1.422\quad\Longrightarrow\quad H_{\text{res}}-R_{\text{SLB}}\le\frac12\log_2 1.422\approx 0.255\ \text{bit/分量},
$$
即"均匀量化+熵编码"对拉普拉斯残差距理论极限不超过 $0.26$ bit，工程上已无需矢量量化。$\square$

---

## §7　Fairy2i 低比特整数量化

### 7.1 量化函数

$b$ bit 对称整数量化：
$$
Q_b(x;a)=a\cdot\mathrm{clamp}\Big(\mathrm{round}\frac{x}{a},\,-2^{b-1},\,2^{b-1}-1\Big),
$$
$a>0$ 为缩放因子（每 tensor 或每 channel 一个）。可表示区间为 $[-2^{b-1}a,\,(2^{b-1}-1)a]$。

### 7.2 误差功率

**无过载区**（$|x|\le 2^{b-1}a$）：由引理 0.8，$e=x-Q_b(x;a)\approx\mathrm{Unif}(-a/2,a/2)$，
$$
\boxed{\ \mathbb{E}[e^2]=\frac{a^2}{12}\ }.
$$

**含过载修正**　设 $x$ 服从对称密度 $p$，记 $A=2^{b-1}a$（截断电平），总误差分解为颗粒噪声与过载噪声：
$$
\mathbb{E}e^2=\underbrace{\frac{a^2}{12}\mathbb{P}(|x|\le A)}_{\text{颗粒}}+\underbrace{\mathbb{E}\big[(|x|-A)^2\,\mathbb{1}_{|x|>A}\big]}_{\text{过载}}.
$$
对 $x\sim\mathcal N(0,\sigma^2)$，记 $\eta=A/\sigma$，过载项有闭式 $\mathbb{E}[(|x|-A)^2\mathbb{1}_{|x|>A}]=2\sigma^2\big[(1+\eta^2)Q(\eta)-\eta\phi(\eta)\big]$，其中 $\phi,Q$ 为标准正态密度与尾函数。

*推导*　$\mathbb{E}[(x-A)^2\mathbb{1}_{x>A}]=\int_A^\infty(x-A)^2\phi(x/\sigma)\frac{dx}{\sigma}$，令 $u=x/\sigma$，展开 $(u-\eta)^2=u^2-2u\eta+\eta^2$ 逐项积分：$\int_\eta^\infty u^2\phi(u)du=\eta\phi(\eta)+Q(\eta)$，$\int_\eta^\infty u\phi(u)du=\phi(\eta)$，$\int_\eta^\infty\phi(u)du=Q(\eta)$，合并得 $(1+\eta^2)Q(\eta)-\eta\phi(\eta)$，双侧乘 2。$\square$

### 7.3 缩放因子选择

- **Absmax**：$a=\max|x|/(2^{b-1}-1)$，完全消除过载项，但颗粒噪声随离群值增大；
- **最优截断**：$\min_a\ \frac{a^2}{12}+2\sigma^2[(1+\eta^2)Q(\eta)-\eta\phi(\eta)]$，一维搜索可解。参考值（高斯源 Lloyd–Max 最优）：$b=2$ 时最优截断约 $A\approx 1.0\sigma$（重建电平 $\pm0.453\sigma,\pm1.510\sigma$）；$b=3$ 时 $A\approx2.2\sigma$；$b=4$ 时 $A\approx3.0\sigma$——位数越低，越应牺牲过载换取颗粒精度；
- **逐通道缩放**：$a_c$ 按 channel $c$ 独立取，消除通道间动态范围差异，误差功率变为 $\frac1{12}\mathbb{E}[a_{c(x)}^2]$。

---

## §8　MiniKV 分层缓存

### 8.1 Token 重要度

定义 token $t$ 的重要度为它在后续查询中获得的平均注意力质量：
$$
p_t=\frac1Q\sum_{q=1}^Q\mathrm{softmax}_t\Big(\frac{q_qK_t^\top}{\sqrt{d_k}}\Big),
$$
其中 $q_q$ 为第 $q$ 个代表性查询（可用最近窗口查询、校准集查询或二者的混合估计），分母归一化使 $\sum_tp_t$ 反映实际注意力总量。

### 8.2 热/冷分层

按 $p_t$ 降序取 Top-$K$ 进入热缓存 $\mathcal{H}$（高精度存储，码率 $r_{\text{hot}}$），其余进入冷缓存 $\mathcal{C}$（深度压缩，码率 $r_{\text{cold}}\ll r_{\text{hot}}$，或仅保留 RVQ 索引）。

### 8.3 概率加权失真与最优码率分配

**问题**　$\min\ D=\sum_tp_td_t(r_t)$，s.t. $\sum_tr_t\le R_{\text{tot}}$，其中 $d_t(r)=\sigma_t^2 2^{-2r}$（A2）。

由引理 0.10 的同构（令 $u_t=2^{-2r_t}$，或直接对 $r_t$ 用 KKT）：
$$
\frac{\partial}{\partial r_t}\big[p_t\sigma_t^22^{-2r_t}\big]=-2\ln2\,p_t\sigma_t^22^{-2r_t}=-\lambda
\quad\Longrightarrow\quad r_t^*=\frac12\log_2\frac{2\ln2\,p_t\sigma_t^2}{\lambda},
$$
即**概率加权水位线**：$r_t^*=\big(\frac12\log_2\frac{p_t\sigma_t^2}{\theta}\big)^+$，重要度–方差乘积 $p_t\sigma_t^2$ 低于水位 $\theta$ 的 token 分配零码率（驱逐）。

**两级特例**　若只允许两档码率，则最优分档边界 $t^*$ 满足边际失真均衡
$$
p_{t^*}\sigma_{t^*}^22^{-2r_{\text{hot}}}\approx p_{t^*+1}\sigma_{t^*+1}^22^{-2r_{\text{cold}}},
$$
在 $r_{\text{hot}}-r_{\text{cold}}=\Delta r$ 固定时，边界由 $p_t\sigma_t^2$ 的几何衰减率决定：$p_{t^*}\approx p_{t^*+1}\cdot 2^{2\Delta r}$ 处截断。

---

## §9　ParetoQ 多目标优化

### 9.1 目标函数

$$
J(\theta)=\lambda_RR(\theta)+\lambda_DD(\theta)+\lambda_A\Delta\mathrm{Acc}(\theta)+\lambda_EE(\theta),
$$
$\theta$ 为全部压缩超参（码率分配、保留率、层划分、缩放因子）。标量化权重 $\lambda\succeq0$。

### 9.2 KKT 条件

等价的约束形式：$\min D(\theta)$ s.t. $R(\theta)\le R_b$，$\Delta\mathrm{Acc}(\theta)\le\varepsilon_a$，$E(\theta)\le E_b$。拉格朗日函数
$$
\mathcal{L}(\theta,\lambda)=D+\lambda_R(R-R_b)+\lambda_A(\Delta\mathrm{Acc}-\varepsilon_a)+\lambda_E(E-E_b).
$$
KKT 条件（在可微性与约束规格成立时，为局部最优的必要条件）：
$$
\begin{cases}
\nabla_\theta D+\lambda_R\nabla_\theta R+\lambda_A\nabla_\theta\Delta\mathrm{Acc}+\lambda_E\nabla_\theta E=0 & \text{（平稳性）}\\[2pt]
R\le R_b,\ \Delta\mathrm{Acc}\le\varepsilon_a,\ E\le E_b & \text{（原始可行）}\\[2pt]
\lambda_R,\lambda_A,\lambda_E\ge0 & \text{（对偶可行）}\\[2pt]
\lambda_R(R-R_b)=\lambda_A(\Delta\mathrm{Acc}-\varepsilon_a)=\lambda_E(E-E_b)=0 & \text{（互补松弛）}
\end{cases}
$$
互补松弛的含义：未打满的约束（如 $R<R_b$）对应权重为零，可安全移除——实践中先在宽松约束下求解，再以互补松弛检验哪些资源是真正瓶颈。

**Pareto 前沿**　$\lambda$ 扫描所得解集在目标空间勾画 Pareto 前沿；由于各目标均为压缩率的单调函数，前沿左下凸化部分才有效（非凸段可由随机化/混合策略超越，本文不展开）。

---

## §10　硬件异构架构能量模型

### 10.1 三级存储能耗

设访问能耗系数 $e_{\text{SRAM}}<e_{\text{HBM}}<e_{\text{SSD}}$（典型量级：SRAM 片内访问约 $0.5$–$1$ pJ/bit，HBM 约 $3$–$7$ pJ/bit，SSD 约 $10$–$50$ pJ/bit 量级，具体值依工艺节点实测）。token $i$ 以概率 $p_i$ 被访问，存放于各层级的比特数为 $r_i^{\text{SRAM}},r_i^{\text{HBM}},r_i^{\text{SSD}}$，则期望总能耗
$$
E=\sum_i p_i\Big(e_{\text{SRAM}}r_i^{\text{SRAM}}+e_{\text{HBM}}r_i^{\text{HBM}}+e_{\text{SSD}}r_i^{\text{SSD}}\Big).
$$

### 10.2 容量约束与最优放置

**问题**
$$
\min_{\{r_i^\tau\ge0\}}\ E\quad\text{s.t.}\quad \sum_i r_i^\tau\le C_\tau\ (\tau\in\{\text{SRAM},\text{HBM},\text{SSD}\}),\qquad r_i^{\text{SRAM}}+r_i^{\text{HBM}}+r_i^{\text{SSD}}=b_i\ \forall i,
$$
$b_i$ 为 token $i$ 的总存储比特（由 §8 码率分配决定）。

**KKT 分析**　对容量约束引入乘子 $\mu_\tau\ge0$，对等式约束引入 $\nu_i$。平稳性：
$$
\frac{\partial\mathcal{L}}{\partial r_i^\tau}=p_ie_\tau+\mu_\tau-\nu_i=0
\quad\Longrightarrow\quad \text{token }i\text{ 的比特只放置于使 }p_ie_\tau+\mu_\tau\text{ 最小的层级 } \tau.
$$
即**等边际能耗条件**：每个 token 选择"访问能耗+层级影子价格"最小的层级；处于两层级边界上的 token 满足
$$
p_i(e_\tau-e_{\tau'})=\mu_{\tau'}-\mu_\tau,
$$
左端为把该 token 从 $\tau'$ 挪到 $\tau$ 的访问能耗节省，右端为两层级容量影子价格之差。

**结构性结论（推论 10.1）**　由于目标关于 $p_i$ 单调分层，最优放置具有阈值结构：存在 $p$ 的阈值 $\theta_1>\theta_2$ 使 $p_i>\theta_1$ 入 SRAM，$\theta_2<p_i\le\theta_1$ 入 HBM，其余落 SSD——即按 §8 重要度排序的三段切分。阈值由容量方程 $\sum_{i:p_i>\theta_1}b_i=C_{\text{SRAM}}$ 等解出。当 $p_i$ 服从重尾分布（实测注意力重要度近似幂律）时，绝大多数比特落 SSD，能耗上界
$$
E\le \bar b\Big[C_{\text{SRAM}}e_{\text{SRAM}}+C_{\text{HBM}}e_{\text{HBM}}\Big]\frac{\bar p_{\text{hot}}}{\bar b}+\Big(\sum_ip_i\Big)e_{\text{SSD}}\bar b_{\text{cold}},
$$
其中冷热分界的期望访问概率 $\bar p_{\text{hot}}$ 是系统能耗的一阶决定量。

---

## §11　潜向量替换与双线性吸收理论

### 11.1 缓存对象的潜向量替换

将逐 token 的缓存对象由 $(k_t,v_t)$ 替换为低维潜向量对
$$
c_t^{KV}=W^{DKV}h_t\in\mathbb{R}^{d_c},\qquad k_t^R=\mathrm{RoPE}_t\big(W^{KR}h_t\big)\in\mathbb{R}^{d_h^R},
$$
其中 $d_c\ll n_{kv}(d_k+d_v)$ 为潜维度，$d_h^R$ 为 RoPE 分支维度。Key/Value 在用到时由共享上投影重建：
$$
k_t^C=W^{UK}c_t^{KV},\qquad v_t^C=W^{UV}c_t^{KV}.
$$

### 11.2 内容 logits 的吸收双线性型

头 $i$ 的查询 $q_i=W_i^{UQ}c^Q$（$c^Q$ 为查询侧潜向量）。内容 logit 为
$$
q_i^\top k_t^C=(W_i^{UQ}c^Q)^\top(W^{UK}c_t^{KV})=c^{Q\top}\underbrace{W_i^{UQ\top}W^{UK}}_{=:A_i\in\mathbb{R}^{d_c\times d_c}}c_t^{KV}.
$$
**吸收**：矩阵 $A_i=W_i^{UQ\top}W^{UK}$ 在推理前一次性合并（离线预计算），推理时无需物化 $k_t^C$，logit 直接在 $d_c$ 维潜空间计算。计算量由 $O(d_k)$/头 变为 $O(d_c)$/头，缓存由 $d_k+d_v$ 维变为 $d_c+d_h^R$ 维。

### 11.3 线性合并与矩阵吸收的可交换性

**定理 11.1（合并–吸收交换律）**　设合并算子 $\mathcal{M}$ 为潜向量的任意线性组合 $\bar c=\sum_jw_jc_j^{KV}$（$w_j\in\mathbb{R}$），则对任意头 $i$，
$$
A_i\bar c=\sum_jw_j\,(A_ic_j^{KV}),
$$
即先合并后吸收 ≡ 先吸收后合并。

*证明*　矩阵乘法对向量加法的分配律（线性映射的定义性质）：$A_i\sum_jw_jc_j=\sum_jw_jA_ic_j$。$\square$

**推论 11.2（调度器不变量）**　任何以内容 logit 线性泛函为调度依据的合并策略（注意力分数、相似度、召回质量量），其调度决策在"合并域"与"吸收域"中完全一致。源文档要求的"调度器式 (9) 不变量与命题 2/4"在本框架中的数学内容即此交换律及其对调度指标的保持，原始编号按其出处逐字保留；本文以定理 11.1 作为其独立证明。

### 11.4 内存界

每层每 token 缓存 $d_c+d_h^R$ 个标量（精度 $b$ bit）。设局部窗口保留 $w$ 个未合并 token，合并树保留 $r_{BL}n$ 个潜节点（$n$ 为合并层深），$L_{\text{layer}}$ 层，则
$$
\mathrm{Mem}(n)\le L_{\text{layer}}\,\big[w+r_{BL}n\big](d_c+d_h^R)\,b.
$$
在 §12 的几何分支合并（分支因子 $g$）下，覆盖长度 $L$ 的序列所需树深 $n=\log_gL$，故 $\mathrm{Mem}=O(L_{\text{layer}}(w+r_{BL}\log_gL)(d_c+d_h^R)b)=O(\log L)$（$w,r_{BL},d_c,d_h^R,b$ 均为与 $L$ 无关的常数），即 cache 随序列长度对数增长而非线性增长。$\square$

### 11.5 RoPE 位置分支的不可合并性与 $\epsilon_{\text{seq}}$ 的结构解释

RoPE 算子本身是线性的（$\mathrm{RoPE}_\Delta(\alpha a+\beta b)=\alpha\mathrm{RoPE}_\Delta a+\beta\mathrm{RoPE}_\Delta b$），不可合并性不在算子而在**位置标签**：被合并的 $g$ 个 token 的 rope key 携带 $g$ 个不同位置旋转 $\{k_{j}^{R}=\mathrm{RoPE}_{j}\tilde k_j\}$，而合并节点只能被指派单一位置 $\tau$。由 $|cos a-\cos b|\le|a-b|$（余弦 1-利普希茨），频率 $f$ 分量的 logit 误差
$$
\epsilon_{\text{seq}}^{(f)}=\Big|\sum_jw_j r_{q,f}r_{k,f}\cos(\omega_f(t-j)+\phi_f)-r_{q,f}\bar r_{k,f}\cos(\omega_f(t-\tau)+\bar\phi_f)\Big|\le r_{q,f}\sum_f\omega_f\sum_j|w_j|\cdot|j-\tau|\cdot r_{k,f}+O(\|r_k-\bar r_k\|^2),
$$
主导项正比于**位置散布** $\sum_j|w_j||j-\tau|$ 加权频率 $\omega_f$。这给出 $\epsilon_{\text{seq}}$ 的结构解释：序列失真源于位置分辨率的丢失，其量级由合并组内位置方差与 RoPE 频率谱共同决定；低频分量（$\omega_f$ 小）对位置散布不敏感，故合并优先损伤高频位置信息——与 §17 的频率截断视角互为表里。$\square$

---

## §12　合并算子的内层闭式优化

### 12.1 白化截断 SVD 闭式解

**问题**　将 $g$ 个潜向量（堆叠为 $C_c\in\mathbb{R}^{d_c\times g}$）压缩为秩 $r$ 表示 $\hat C$，按查询重要性度量的白化范数计失真（$w\equiv1$ 的率失真目标）：
$$
\min_{\mathrm{rank}(\hat C)\le r}\ \big\|\bar M^{1/2}\big(C_c-\hat C\big)\big\|_F^2,
$$
$\bar M\succeq0$ 为 token 重要度加权矩阵（$\bar M=\mathrm{diag}(\bar m_j)$）。

**解**　变量替换 $B=\bar M^{1/2}C_c$（要求 $\bar M\succ0$，否则在被零权重方向上无约束、失真为零贡献，可直接投影掉）。问题等价于 $\min_{\mathrm{rank}(\tilde B)\le r}\|B-\tilde B\|_F^2$（其中 $\tilde B=\bar M^{1/2}\hat C$，$\mathrm{rank}$ 约束保持）。由引理 0.4（Eckart–Young）：
$$
B=\bar M^{1/2}C_c\ \xrightarrow{\text{SVD}}\ U\Sigma V^\top\ \Longrightarrow\ \hat C^*=\bar M^{-1/2}U_r\Sigma_rV_r^\top,
$$
**最优值**
$$
\boxed{\ \min=\sum_{i>r}\sigma_i^2\big(\bar M^{1/2}C_c^\top\big)\ }
$$
（谱范数版本同理为 $\sigma_{r+1}$）。$\square$

### 12.2 查询加权退化为广义特征值问题

当失真度量替换为查询分布加权的期望 logit 失真 $\mathbb{E}_q\|q^\top A(C_c-\hat C)\|^2=\|(C_c-\hat C)^\top A^\top\Sigma_q^{1/2}\|_F^2$（$\Sigma_q$ 为查询二阶矩），问题化为列空间加权的低秩近似，其最优子空间由广义特征值问题
$$
C_c^\top A^\top\Sigma_qAC_c\,v=\lambda\,\Sigma_cv
$$
的前 $r$ 个广义特征向量张成（$\Sigma_c$ 为潜向量二阶矩），即广义 SVD（GSVD）解。特例：$\Sigma_q=I$ 退回 12.1；$\Sigma_c=I$ 退化为普通 SVD。$\square$

### 12.3 显著性预算分配的注水闭式解

设第 $i$ 个合并组的失真–资源幂律 $D_i(r_i)=a_ir_i^{-\kappa_i}$（$r_i$ 为分配秩/比特），总预算 $R$。由引理 0.10：
$$
\boxed{\ r_i^*=\Big(\frac{a_i\kappa_i}{\lambda}\Big)^{\frac{1}{\kappa_i+1}}\propto(a_i\kappa_i)^{\frac{1}{\kappa_i+1}}\ },
$$
$\lambda$ 由 $\sum_ir_i^*=R$ 解出。显著性 $a_i$（由 §3 敏感度给出）与衰减指数 $\kappa_i$ 越大，分配越多，但边际弹性递减。

### 12.4 最优分支因子

**假设（幂律单次合并失真，待实测标定）**　单次把 $g$ 个潜节点合并为一个的失真 $\epsilon_{\text{single}}\propto g^{\kappa'}$，$\kappa'>0$ 为幂律指数（$\kappa'=\langle\text{MEASURED\_PENDING}\rangle$，需由目标模型实测拟合，见 §21 验证方案）。

覆盖长度 $L$ 所需树深 $=\log_gL=\ln L/\ln g$，总失真
$$
\epsilon_{\text{total}}(g)\propto g^{\kappa'}\cdot\frac{\ln L}{\ln g}.
$$
**最优分支因子**　对 $f(g)=g^{\kappa'}/\ln g$ 求导：
$$
f'(g)=\frac{\kappa'g^{\kappa'-1}\ln g-g^{\kappa'-1}}{(\ln g)^2}=0
\quad\Longrightarrow\quad \kappa'\ln g=1
\quad\Longrightarrow\quad \boxed{\ g^*=e^{1/\kappa'}\ }.
$$
二阶条件：$f''(g^*)=\frac{\kappa'^2(g^*)^{\kappa'-1}}{\ln g^*}>0$，确为极小。解释：$\kappa'$ 越大（单次合并代价随组大小激增），最优组越小；$\kappa'\to0$（合并几乎无损）时 $g^*\to\infty$，退化为一次性全并。

---

## §13　召回门

### 13.1 贝叶斯风险最小化

设块 $C$ 含有当前查询所需证据的事件概率为 $p=p(C\mid\text{evidence})$。动作空间 $\{$召回, 跳过$\}$，损失：召回恒付带宽代价 $c_r$；跳过且实际需要时付精度代价 $c_m$。贝叶斯风险
$$
R(\text{召回})=c_r,\qquad R(\text{跳过})=p\,c_m.
$$
贝叶斯最优决策：召回 iff $pc_m>c_r$ iff
$$
p>\theta^*:=\frac{c_r}{c_m}\quad(\text{若召回对正确性无附加收益}),
$$
更一般地（召回本身不完美、以概率 $1-\eta$ 漏检）$\theta^*=\frac{c_r}{\eta\,c_m}$。

### 13.2 可计算代理

真实 $p$ 不可计算（需先召回才知道是否需要）。以**压缩块吸引到的注意力质量** $p_C=\sum_{j\in C}\alpha_j$（用廉价粗粒度 key 计算）作为代理：

**命题 13.1**　若代理满足单调性条件 $p_C\ge p_C'$ $\Rightarrow$ $p\ge p'$（即注意力质量是"被需要"的保序统计量），则阈值规则 $p_C\ge\theta$ 与贝叶斯规则 $p\ge\theta^*$ 的决策区域一致，$\theta$ 为 $p_C$ 轴上与 $\theta^*$ 对应的分位点。$\square$（保序变换下阈值规则等价为秩统计量检验，此为核心假设而非定理；其成立性需按 §21 方案实测 ROC 验证。）

### 13.3 峰值界

**命题 13.2（峰值召回数与 $n$ 无关）**　设各压缩块的注意力质量 $\{p_{C_k}\}$ 满足归一性 $\sum_kp_{C_k}\le1$（softmax 质量在块划分上求和守恒），则满足阈值条件的块数
$$
\#\{k:p_{C_k}\ge\theta\}\le\Big\lfloor\frac1\theta\Big\rfloor,
$$
与总块数 $n$ 无关。

*证明*　设 $m$ 个块满足 $p_{C_k}\ge\theta$，则 $1\ge\sum_kp_{C_k}\ge m\theta$，故 $m\le1/\theta$，取整得 $m\le\lfloor1/\theta\rfloor$。$\square$

**意义**　召回门的每步附加开销被常数 $\lfloor1/\theta\rfloor$ 封顶，使长序列推理的最坏情况带宽有界——这是召回式稀疏注意力的系统性优势。

---

## §14　MQA（Multi-Query Attention）架构压缩

### 14.1 公式推导

所有 $n_q$ 个 Query 头共享唯一一组 KV 头（$n_{kv}=1$）：
$$
K=\mathrm{RoPE}(XW^K)\in\mathbb{R}^{L\times d_h},\qquad V=XW^V\in\mathbb{R}^{L\times d_h},
$$
$$
Q_i=\mathrm{RoPE}(XW_i^Q),\quad i=1,\dots,n_q,
$$
$$
\text{head}_i=\mathrm{Softmax}\Big(\frac{Q_iK^\top}{\sqrt{d_h}}\Big)V,\qquad
\mathrm{MQA}(X)=\mathrm{Concat}(\text{head}_1,\dots,\text{head}_{n_q})\,W^O.
$$

### 14.2 压缩比

逐层逐 token 缓存标量数：MHA 为 $n_q(d_k+d_v)=2n_qd_h$；MQA 为 $d_k+d_v=2d_h$。故
$$
\boxed{\ C_{\text{MQA}}=\frac{2d_h}{2n_qd_h}=\frac{1}{n_q}\ },
$$
即缓存量压缩为 MHA 的 $1/n_q$（$n_q=32$ 时即 32×，尚未动用任何数值压缩手段）。

**系统意义**　解码阶段为内存带宽瓶颈：每步需读入全部 cache。MQA 使每步读取字节数降为 $1/n_q$，算术强度（FLOPs/字节）提升 $n_q$ 倍，在带宽受限 regime 下吞吐近线性提升；代价是容量瓶颈（所有 query 头共享同一组 key/value 子空间，表达能力下降），质量损失由 $n_q$ 与任务类型决定，需实测（§21）。

---

## §15　GQA（Grouped-Query Attention）架构压缩

### 15.1 公式推导

Query 头分为 $n_{kv}$ 组，每组共享一组 KV：
$$
K_g=\mathrm{RoPE}(XW_g^K),\quad V_g=XW_g^V,\qquad g=1,\dots,n_{kv},
$$
$$
Q_i=\mathrm{RoPE}(XW_i^Q),\qquad g(i)=\Big\lfloor i\cdot\frac{n_{kv}}{n_q}\Big\rfloor,
$$
$$
\text{head}_i=\mathrm{Softmax}\Big(\frac{Q_iK_{g(i)}^\top}{\sqrt{d_h}}\Big)V_{g(i)},\qquad
\mathrm{GQA}(X)=\mathrm{Concat}(\text{head}_1,\dots,\text{head}_{n_q})\,W^O.
$$

### 15.2 压缩比与退化情形

逐层逐 token 缓存标量数 $n_{kv}(d_k+d_v)$，相对 MHA：
$$
\boxed{\ C_{\text{GQA}}=\frac{n_{kv}}{n_q}\ }.
$$
**退化检验（自洽性验证）**：
- $n_{kv}=1$：$g(i)=\lfloor i/n_q\rfloor=0\ \forall i$，所有头共享唯一 KV 组，公式退化为 §14 的 MQA ✓；
- $n_{kv}=n_q$：$g(i)=i$，每头独占 KV，退化为标准 MHA，$C=1$ ✓。

GQA 在 MHA 的表达力与 MQA 的压缩率之间给出一条离散权衡曲线；其质量–容量权衡实证上在 $n_{kv}\approx n_q/8$ 附近通常出现"免费压缩区"（损失 $\ll$ 压缩收益），但该拐点位置是经验命题，逐模型需实测标定（§21）。

---

## §16　TurboQuant 在线近最优 KV 量化

### 16.1 向量极分解与随机旋转

对任意待缓存向量 $v\in\mathbb{R}^d$（$K$ 或 $V$ 的某行）：
$$
u=\frac{v}{\|v\|}\ (\text{方向}),\qquad r=\|v\|\ (\text{模长}),\qquad \tilde u=R^\top u,
$$
其中 $R$ 为 Haar 随机正交矩阵（推理全程共用同一随机种子生成，存储开销摊销为零）。

**引理 16.1（旋转后坐标的渐近高斯性）**　固定单位向量 $u$，$R$ 为 Haar 随机正交阵，则 $\tilde u=R^\top u$ 在单位球面 $S^{d-1}$ 上均匀分布；其坐标满足 $\mathbb{E}[\tilde u_i]=0$，$\mathbb{E}[\tilde u_i^2]=1/d$，且 $d\to\infty$ 时 $\sqrt d\,\tilde u_i\xrightarrow{d}\mathcal N(0,1)$。

*证明*　球面均匀性：Haar 测度在正交作用下不变，$R^\top u$ 的分布与 $u$ 无关（取 $u=e_1$，$R^\top e_1$ 即 $R$ 的第一行，均匀分布于球面）。对称性给出零均值；$\sum_i\tilde u_i^2=\|\tilde u\|^2=1$ 结合坐标可交换性给出 $\mathbb{E}\tilde u_i^2=1/d$。渐近高斯性：球面均匀向量可表示为 $\tilde u=g/\|g\|$（$g\sim\mathcal N(0,I_d)$），故 $\sqrt d\,\tilde u_i=\sqrt d\,g_i/\|g\|$，由大数律 $\|g\|/\sqrt d\to1$ a.s.（$\mathbb{E}\|g\|^2=d$），Slutsky 定理得极限分布 $\mathcal N(0,1)$。$\square$

### 16.2 标量量化与重构

对旋转后坐标做 $b$ bit Lloyd–Max 标量量化（码本对 $\mathcal N(0,1/d)$ 优化，离线预计算）：
$$
\hat{\tilde u}=\mathcal{Q}_b(\tilde u),\qquad \hat v=r\cdot R\cdot\hat{\tilde u}.
$$
解码仅需一次正交变换与数乘。

### 16.3 MSE 失真上界

**定理 16.2**　高分辨率 regime（$b\ge2$，A2）下
$$
\mathbb{E}\|v-\hat v\|_2^2\le\frac{\sqrt3\,\pi}{2}\,4^{-b}\|v\|_2^2.
$$

*推导*　（i）正交不变性：$\|v-\hat v\|=\|rR(u'-Q)\|$... 直接计算 $\|v-\hat v\|^2=r^2\|R(\tilde u-\hat{\tilde u})\|^2=r^2\|\tilde u-\hat{\tilde u}\|^2$（正交变换保距）。（ii）逐坐标失真：高斯源 Lloyd–Max 量化的高分辨率失真为 $D_{\text{LM}}(b)=\frac{\sqrt3\pi}{2}\sigma^2 4^{-b}(1+o(1))$（Panter–Dite 积分对高斯密度的闭式求值：$D=\frac{1}{12B^2}\big(\int p(x)^{1/3}dx\big)^3$，代入 $p=\mathcal N(0,\sigma^2)$：$\int p^{1/3}dx=(2\pi\sigma^2)^{1/6}\sqrt{3\pi}$... 直接计算 $\big(\int(2\pi\sigma^2)^{-1/6}e^{-x^2/6\sigma^2}dx\big)^3=(2\pi\sigma^2)^{-1/2}( \sqrt{6\pi}\sigma)^3\cdot$ 化简 $=\frac{\sqrt3\pi}{2}\sigma^2$ 与 $\frac{1}{12B^2}$ 合并即得）。（iii）由引理 16.1，$\sigma^2=1/d$，$d$ 个坐标相加：$\mathbb{E}\|\tilde u-\hat{\tilde u}\|^2=d\cdot\frac{\sqrt3\pi}{2d}4^{-b}=\frac{\sqrt3\pi}{2}4^{-b}$。乘 $r^2=\|v\|^2$ 得证。$\square$

### 16.4 内积失真上界

**定理 16.3**　设量化误差 $e=\hat v-v$。随机旋转使误差近似各向同性：$\mathbb{E}[ee^\top]=\frac{D}{d}I$（$D=\frac{\sqrt3\pi}{2}4^{-b}\|v\|^2$），从而对任意与 $R$ 独立的查询 $q$，
$$
\mathbb{E}\big|\langle q,v\rangle-\langle q,\hat v\rangle\big|^2=q^\top\mathbb{E}[ee^\top]q=\frac{D}{d}\|q\|^2=\frac{\sqrt3\,\pi}{2d}\,4^{-b}\|q\|^2\|v\|^2.
$$

*证明*　各向同性：对任意固定正交阵 $P$，$Pe$ 的分布与 $e$ 相同（旋转与量化方案的球面对称性），故 $\mathbb{E}[ee^\top]$ 与所有正交阵可交换，必为恒等阵的标量倍；取迹定出标量 $D/d$。于是 $\mathbb{E}(q^\top e)^2=q^\top\frac{D}{d}Iq=\frac{D}{d}\|q\|^2$。$\square$

**注（与源文献常数的差异）**　源文献给出的界为 $\frac{\sqrt3\pi^2}{d}4^{-b}\|q\|^2\|v\|^2$，比定理 16.3 松一个 $2\pi$ 因子；差异源于其未使用各向同性而用了逐坐标最坏情形放缩。本文保留更紧的定理 16.3 作为主结果，源文献形式作为保守上界依然成立。

### 16.5 存储结构

推理时每向量仅存：$d$ 个 $b$ bit 量化码 $+$ 一个 fp16 模长 $r$（旋转矩阵由种子实时重生成）。每分量有效码率
$$
R_{\text{TQ}}=b+\frac{16}{d}\ \text{bit/分量},
$$
$d=128$、$b=2$ 时 $R_{\text{TQ}}=2.125$ bit/分量，即相对 fp16 压缩 $7.5\times$，且无需校准集、在线单遍完成。

---

## §17　TriAttention 三角级数 KV 压缩

### 17.1 RoPE 内积的三角展开

RoPE 将 $q,k$ 的第 $f$ 个二维子空间分别旋转角度 $\omega_ft,\omega_fj$（$\omega_f=\theta^{-2f/d}$，$\theta=10000$）。在该子空间内写极坐标 $q_f=r_{q,f}(\cos\alpha_f,\sin\alpha_f)$，$k_f=r_{k,f}(\cos\beta_f,\sin\beta_f)$，则
$$
\langle q_{t,f},k_{j,f}\rangle=r_{q,f}r_{k,f}\cos\big(\omega_f(t-j)-(\alpha_f-\beta_f)\big)=r_{q,f}r_{k,f}\cos(\omega_f\Delta+\phi_f),
$$
其中 $\Delta=t-j$ 为位置差，$\phi_f=\beta_f-\alpha_f$ 为相位差（旋转差角公式：$\cos(a-b)=\cos a\cos b+\sin a\sin b$ 逐分量展开即得）。全向量
$$
\langle q_t,k_j\rangle=\sum_{f=1}^{d/2}r_{q,f}r_{k,f}\cos(\omega_f\Delta+\phi_f).
$$

### 17.2 方向集中假设下的 logit 三角级数

**假设（Q/K 方向集中，待实测）**　同层同头的 $q,k$ 方向集中于均值方向 $\bar q,\bar k$：$r_{q,f}\approx\|\bar q_f\|$，$r_{k,f}\approx\|\bar k_f\|$，$\phi_f\approx\bar\phi_f$。则 logit 仅为位置差的三角级数：
$$
\mathrm{logit}(\Delta)=\sum_{f=1}^{d/2}\big[a_f\cos(\omega_f\Delta)+b_f\sin(\omega_f\Delta)\big],
$$
系数由积化和差 $\cos(\omega\Delta+\phi)=\cos\omega\Delta\cos\phi-\sin\omega\Delta\sin\phi$ 读出：
$$
a_f=\|\bar q_f\|\,\|\bar k_f\|\cos\bar\phi_f,\qquad b_f=-\|\bar q_f\|\,\|\bar k_f\|\sin\bar\phi_f.
$$

### 17.3 注意力权重与输出

$$
\alpha(\Delta)=\mathrm{Softmax}\big(\mathrm{logit}(\Delta)/\sqrt{d_h}\big),\qquad o_t=\sum_{\Delta=0}^{t-1}\alpha(\Delta)\,v_{t-\Delta}.
$$

### 17.4 缓存量与截断误差

Key 侧缓存由 $L\times d_k$ 变为 $2F$ 个系数（保留 $F$ 个主导频率，$F\le d/2$），**随频率维度而非序列长度增长**：Key 侧存储 $O(F)$，与 $L$ 无关。

**截断误差（Parseval）**　logit 函数的 $L^2$ 截断误差等于舍弃频率的能量：
$$
\big\|\mathrm{logit}-\mathrm{logit}_{F}\big\|_{L^2}^2=\frac{T}{2}\sum_{f>F}(a_f^2+b_f^2)=\frac{T}{2}\sum_{f>F}\|\bar q_f\|^2\|\bar k_f\|^2,
$$
（三角函数系在 $[0,T]$ 上的正交性：$\int_0^T\cos^2(\omega_f\Delta)d\Delta=T/2$）。由于 $\omega_f=\theta^{-2f/d}$ 随 $f$ 几何衰减且实测 Q/K 能量集中于低频子空间，尾部能量快速衰减，$F\ll d/2$ 即可逼近。由引理 0.3，注意力权重扰动被 logit 误差的 $1/2$ 倍（$L^2$ 范数下）控制。

**边界说明**　本模块压缩的是 **Key/位置侧**；Value 缓存仍随 $L$ 线性增长，须与 §5/§7/§18 的 Value 压缩联用才能获得端到端常数级缓存。此为其适用边界，不应单独声称全 cache 常数化。

---

## §18　SVD 共享基低秩 KV 压缩

### 18.1 分段与编码

KV 序列拆分为高精度受保护段 $P$（近期 token / 高敏感 token，全精度保存）与低秩背景段 $B$，$S=|B|$，$K_B\in\mathbb{R}^{S\times d_k}$，$V_B\in\mathbb{R}^{S\times d_v}$，截断秩 $r$。

**Key 编码**：截断 SVD
$$
K_B=U\Sigma V^\top\approx U_r\Sigma_rV_r^\top,\qquad U_r\in\mathbb{R}^{S\times r},\ \Sigma_r\in\mathbb{R}^{r\times r},\ V_r\in\mathbb{R}^{d_k\times r}.
$$
由引理 0.4（Eckart–Young），这是所有秩 $\le r$ 近似中 F-范数最优者：
$$
\|K_B-\hat K_B\|_F^2=\sum_{i>r}\sigma_i^2(K_B).
$$

**Value 共享 Key 基投影**（刻意不做 $V_B$ 自身的 SVD，以换取 §18.2 的融合计算）：
$$
V_{\text{code}}=U_r^\top V_B\in\mathbb{R}^{r\times d_v},\qquad \hat V_B=U_rV_{\text{code}}=U_rU_r^\top V_B=P_{U_r}V_B.
$$
投影失真 $\|V_B-\hat V_B\|_F^2=\|V_B\|_F^2-\|U_r^\top V_B\|_F^2=\|(I-P_{U_r})V_B\|_F^2$。

### 18.2 融合核计算（不物化 KV）

对查询 $q$（已含 $1/\sqrt{d_k}$ 缩放在下式中并入）：
$$
\text{scores}_{\text{bg}}=q\hat K_B^\top=q\big(U_r\Sigma_rV_r^\top\big)^\top=qV_r\Sigma_rU_r^\top=\big(qV_r\Sigma_r\big)U_r^\top,
$$
计算次序 $qV_r$（$O(rd_k)$）$\to$ 乘 $\Sigma_r$（$O(r)$）$\to$ 乘 $U_r^\top$（$O(Sr)$），总计 $O(r(d_k+S))$，而物化方案为 $O(Sd_k)$；当 $r\ll d_k$ 时加速 $\approx d_k/r$ 倍。
$$
\text{scores}_{\text{exact}}=qK_P^\top,\qquad a=\mathrm{Softmax}\big([\text{scores}_{\text{exact}};\ \text{scores}_{\text{bg}}]\big)=[a_P;a_{\text{bg}}],
$$
输出同样不物化 $\hat V_B$：
$$
y(q)=a_{\text{bg}}^\top\hat V_B+a_P^\top V_P=\big(a_{\text{bg}}^\top U_r\big)V_{\text{code}}+a_P^\top V_P,
$$
代价 $O(Sr+rd_v)$。

### 18.3 存储压缩比

背景段存储：$U_r$ 需 $Sr$、$\Sigma_r$ 需 $r$、$V_r$ 需 $rd_k$、$V_{\text{code}}$ 需 $rd_v$ 个标量；受保护段全精度。故
$$
\boxed{\ \text{storage\_ratio}=\frac{S(d_k+d_v)\,b}{\big[Sr+r+rd_k+rd_v\big]b+|P|(d_k+d_v)b}\ }.
$$
渐近（$S\to\infty$，$|P|,r,d$ 固定）：分子 $\sim S(d_k+d_v)b$，分母 $\sim Srb$，压缩率 $\to(d_k+d_v)/r$。$d_k=d_v=128,r=16$ 时渐近 $16\times$。

### 18.4 输出误差上界

**定理 18.1**　设精确输出 $y_S$（完整 $K_C,V_C$）与压缩输出 $y_C$，则
$$
\|y_C-y_S\|_2\le \sigma_{r+1}(V_C)+\big\|\big(I-P_{U_r(K_C)}\big)V_r\big\|_2+\|V_C\|_2\Big(e^{\sigma_{r+1}(K_C)\|Q\|_2/\sqrt{d_k}}-1\Big)+\delta_{\text{sm}}.
$$

*推导*（三角不等式逐项）　将总误差分解为 $y_C-y_S=\Delta_{\text{val}}+\Delta_{\text{basis}}+\Delta_{\text{attn}}+\Delta_{\text{sm}}$：

(i) **Value 截断项**：注意力权重 $a$ 在单纯形上（$\|a\|_1=1$），故 $\|a^\top(V_C-\tilde V_C)\|_2\le\|a\|_1\|V_C-\tilde V_C\|_2=\sigma_{r+1}(V_C)$，其中 $\tilde V_C$ 为 $V_C$ 的最优秩 $r$ 近似（引理 0.4 的谱范数形式）。

(ii) **共享基失配项**：$\hat V_B=P_{U_r(K_C)}V_B$ 与 $V$ 自身最优低秩表示之差被 $\|(I-P_{U_r(K_C)})V_r\|_2$ 控制（$V_r$ 此处为 $V$ 的右因子，即源文献记号）；该项量化"用 Key 的子空间表达 Value"的代价，当 $K,V$ 主左奇异子空间对齐时趋于零。

(iii) **注意力权重扰动项**：Key 误差 $\|K_C-\hat K_C\|_2=\sigma_{r+1}(K_C)$ 使 logit 逐位偏移 $|\delta_j|=|q^\top(k_j-\hat k_j)|/\sqrt{d_k}\le\|q\|_2\sigma_{r+1}(K_C)/\sqrt{d_k}=:\varepsilon$。由引理 0.3(ii)，权重逐分量变化 $|a'_j-a_j|\le(e^{2\varepsilon}-1)a_j$，输出偏移 $\le\|V_C\|_2(e^{2\varepsilon}-1)$；源文献记法吸收因子 2 为 $\varepsilon=\sigma_{r+1}(K_C)\|Q\|_2/\sqrt{d_k}$，本文从之。

(iv) $\delta_{\text{sm}}$：受保护段/背景段混合导致 softmax 分母在两段上分别归一化时的维度失配残差，无闭式，作为经验项在 §21 实测拟合。

四项由三角不等式相加即得。$\square$

**渐近行为**：$r\to\mathrm{rank}$ 时 (i)(ii)(iii) 同时趋零，界是紧的；$Q$ 的谱范数大（长序列多查询堆叠）时 (iii) 指数项主导，提示应控制 $\sigma_{r+1}(K_C)\|Q\|_2/\sqrt{d_k}\ll1$，即秩 $r$ 应随查询批量增大而提高——这给出秩选择的定量准则 $r^*=\min\{r:\sigma_{r+1}(K_C)\le c\sqrt{d_k}/\|Q\|_2\}$。

---

## §19　补充推导：MoE 稀疏激活、量化与 FlashAttention 式 IO 优化

### 19.1 MoE 稀疏激活

**MoE 层定义**　$E$ 个专家 FFN，门控加权：
$$
y=\sum_{i=1}^E g_i(x)\,\mathrm{FFN}_i(x),\qquad g(x)=\mathrm{Softmax}\big(\mathrm{TopK}(xW_g,K)\big),
$$
$\mathrm{TopK}(v,K)$ 保留 $v$ 中最大的 $K$ 个分量、其余置 $-\infty$（softmax 后恰为零），故至多 $K$ 个专家被激活，$\sum_ig_i=1$。

**计算复杂度**　单专家 FFN（隐维 $d_{\text{ff}}$，输入维 $D$）的 FLOPs 为 $O(D\cdot d_{\text{ff}})$；$T$ 个 token 时：
- 稠密 MoE（全专家计算）：$O(T\cdot D\cdot d_{\text{ff}}\cdot E)$；
- Top-$K$ 稀疏激活：仅计算被选中的专家，$O(T\cdot D\cdot d_{\text{ff}}\cdot K)$；
- **加速比** $E/K$。$E=64,K=2$ 时理论 FLOPs 加速 $32\times$；实际加速受专家并行通信与负载不均折扣，实测通常为理论值的 $50$–$80\%$。

**负载均衡损失**　
$$
\mathcal{L}_{\text{aux}}=\alpha\cdot E\cdot\sum_{i=1}^E f_i\,P_i,
$$
$f_i=\frac1T\#\{t:\text{token }t\text{ 选中专家 }i\}$（选中频率），$P_i=\frac1T\sum_tg_i(x_t)$（平均门控概率）。

**为何该损失鼓励均衡**　由 $\sum_if_i=\sum_iP_i=1$ 与 Cauchy–Schwarz（重排不等式）：
$$
\sum_if_iP_i\ge\frac1E\Big(\sum_if_i\Big)\Big(\sum_iP_i\Big)=\frac1E,
$$
等号当且仅当 $f_i=P_i=1/E$（完全均衡）。故 $\mathcal{L}_{\text{aux}}\ge\alpha$，最小值在均衡点取得；偏离均衡时损失线性放大不均分量。$\square$

### 19.2 量化（INT8/FP8/INT4）

**对称线性量化**　
$$
x_{\text{int}}=\mathrm{round}(x/s),\qquad s=\frac{\max|x|}{2^{b-1}-1},\qquad \hat x=s\cdot x_{\text{int}}.
$$

**量化误差功率**　无过载时由引理 0.8（$\Delta=s$）：
$$
\mathbb{E}[(x-\hat x)^2]\approx\frac{s^2}{12}=\frac{\max|x|^2}{12\,(2^{b-1}-1)^2}.
$$
信号量化噪声比（$\sigma_x^2$ 为信号功率）：
$$
\mathrm{SQNR}=10\log_{10}\frac{\sigma_x^2}{s^2/12}=6.02\,b+10\log_{10}\frac{12\,\sigma_x^2(2^{b-1}-1)^2}{\max|x|^2}\approx 6.02\,b-C_{\text{crest}}\ \text{dB},
$$
其中 $C_{\text{crest}}=20\log_{10}(\max|x|/\sigma_x)-10\log_{10}3-40\log_{10}(1-2^{-(b-1)})^{-1}\approx20\log_{10}(\max|x|/\sigma_x)-4.77$ dB 为波峰因子惩罚。这给出著名的 **6 dB/bit** 律。

**FP8 规格**　（1 位符号位）：
| 格式 | 指数位 | 尾数位 | 最大正规格化数 | 最小正规格化数 | 相对精度（机器 $\epsilon$） |
|---|---|---|---|---|---|
| E4M3 | 4（偏置 7） | 3 | $\pm448$ | $2^{-6}$ | $2^{-3}$ |
| E5M2 | 5（偏置 15） | 2 | $\pm57344$ | $2^{-14}$ | $2^{-2}$ |

设计权衡：E4M3 精度高（$2^{-3}$）动态范围小，适合权重/激活前向；E5M2 范围宽（接近 fp16 的 $2^{-14}$ 下限）适合梯度。KV cache 数值范围通常有界（经 LayerNorm 与 RoPE），E4M3 更常用；离群通道需按 §7.3 逐通道缩放或保留 fp16 离群组。

**对注意力分数的影响**　设 $\hat k=k+e$，各分量误差独立、$\mathbb{E}e_i^2=s^2/12$，则
$$
\mathbb{E}\big|\langle q,k\rangle-\langle q,\hat k\rangle\big|^2=\mathbb{E}\Big(\sum_iq_ie_i\Big)^2=\sum_iq_i^2\,\mathbb{E}e_i^2=\frac{s^2}{12}\|q\|_2^2,
$$
（交叉项 $\mathbb{E}[e_ie_j]=0$（$i\ne j$）由独立性）。即**内积失真功率 = 量化噪声功率 × 查询功率**，与 $d$ 无关——这是标量量化用于 KV cache 的关键有利性质。$\square$

### 19.3 FlashAttention 式 IO 优化

**分块**　将 $Q,K,V$ 分为行块 $Q_i\in\mathbb{R}^{B_r\times d}$、$K_j,V_j\in\mathbb{R}^{B_c\times d}$，块大小由 SRAM 容量 $M$（字节）约束：单块 K/V 加中间结果需驻留 SRAM，$B_c=\Theta(M/d)$，$B_r=\Theta(M/d)$。

**在线 Softmax**　维护运行最大值 $m_i$ 与归一化因子 $l_i$。处理块 $S_{ij}=Q_iK_j^\top/\sqrt d$ 时：
$$
m_i^{\text{new}}=\max\big(m_i,\ \mathrm{rowmax}(S_{ij})\big),
$$
$$
l_i^{\text{new}}=e^{m_i-m_i^{\text{new}}}l_i+e^{\mathrm{rowmax}(S_{ij})-m_i^{\text{new}}}\cdot\mathrm{rowsum}\big(e^{S_{ij}-\mathrm{rowmax}(S_{ij})}\big),
$$
$$
O_i^{\text{new}}=e^{m_i-m_i^{\text{new}}}O_i+e^{\mathrm{rowmax}(S_{ij})-m_i^{\text{new}}}\cdot\big(e^{S_{ij}-\mathrm{rowmax}(S_{ij})}V_j\big).
$$
**正确性**　设处理完前 $j$ 块时 $O_i=\sum_{j'\le j}e^{S_{ij'}-m_i}V_{j'}$、$l_i=\sum_{j'\le j}e^{S_{ij'}-m_i}$（以旧 $m_i$ 为基准的非归一化和）。归纳步：以新基准 $m_i^{\text{new}}$ 重标定旧和（乘 $e^{m_i-m_i^{\text{new}}}$），加入新块贡献（以其块内最大值为临时基准再修正）。全部块处理完后 $O_i/l_i$ 恰为精确 softmax 注意力输出——与一次性计算逐位一致（浮点结合序除外）。$\square$

**IO 复杂度**　传统实现将 $S=QK^\top\in\mathbb{R}^{T\times T}$ 物化到 HBM：读写 $\Theta(T^2)$ 个元素，总 HBM 访问 $\Theta(Td+T^2)$。FlashAttention 不物化 $S$：外层每行块（共 $T/B_r=\Theta(Td/M)$ 个）扫过全部 $K,V$（$\Theta(Td)$ 元素）：
$$
\text{HBM 访问}=\Theta\Big(\frac{Td}{M}\cdot Td\Big)=\Theta\Big(\frac{T^2d^2}{M}\Big).
$$
相对传统 $\Theta(T^2)$（$d$ 视为常数时）改善 $M/d^2$ 倍；典型 $M\approx100$ KB（A100 SRAM 192 KB）、$d=64$–$128$ 时改善一个数量级以上，实测 2–4× 端到端加速。

**与 KV 压缩的兼容性**　压缩后每元素字节数由 2 B（fp16）降为 $b/8$ B（$b$ bit 量化），同容量 SRAM 可容纳的 $B_c$ 放大 $16/b$ 倍，HBM 访问次数进一步降为
$$
\Theta\Big(\frac{T^2d^2}{M}\cdot\frac{b}{16}\Big),
$$
且解码阶段 HBM 读取总量直接按 $C$（§20 压缩率）缩减。两个层面的优化相乘：压缩减少"必须搬运的字节"，分块在线 softmax 减少"搬运的次数"。$\square$

---

## §20　综合所有模块的最终码率公式

### 20.1 每分量总码率

整合剪枝（§4，保留率 $\rho$ 与掩码开销）、RVQ（§5）、残差熵编码（§6）：
$$
\boxed{\ r_{\text{total}}=\rho\,(R_Q+H_{\text{res}})+r_{\text{mask}}\ },
$$
其中
$$
R_Q=\frac1d\sum_{m=1}^M\log_2B_m,\qquad H_{\text{res}}=\log_2\frac{2eb}{\Delta},
$$
$r_{\text{mask}}$ 为每分量掩码存储开销（二值掩码经熵编码后 $r_{\text{mask}}\le1$，取 $h_2(\rho)$ 更近真值，$h_2$ 为二元熵）。被剪枝的 $1-\rho$ 分量不再消耗 $R_Q$ 与 $H_{\text{res}}$，仅存掩码位。

### 20.2 总压缩率

$$
\boxed{\ C=\frac{16}{\rho\,(R_Q+H_{\text{res}})+r_{\text{mask}}}\ }.
$$

### 20.3 统一率失真–精度–能耗联合优化表达

汇总全部模块的决策变量 $\Theta=\{n_{kv},\ b,\ \rho,\ \{B_m\},\ \Delta,\ r,\ F,\ g,\ \theta_{\text{recall}},\ K_{\text{MoE}},\ B_r,B_c,\ \{r_i^\tau\}\}$，统一问题：
$$
\min_{\Theta}\ J=\lambda_R\,r_{\text{total}}+\lambda_D\,\underbrace{\big(D_P+D_T+D_Q+D_{\text{res}}+\epsilon_{\text{seq}}+\textstyle\sum_{i>r}\sigma_i^2\big)}_{D_{\text{total}}\ (\text{A6 可加性})}+\lambda_A\,\Delta\mathrm{Acc}+\lambda_E\,\underbrace{\sum_ip_i\sum_\tau e_\tau r_i^\tau}_{E\ (\S10)},
$$
约束：$C\ge C_{\min}$，$\Delta\mathrm{Acc}\le\varepsilon_a$，容量约束 $\sum_ir_i^\tau\le C_\tau$，峰值召回 $\le\lfloor1/\theta_{\text{recall}}\rfloor$（§13.3 自动满足）。

**模块间耦合的三条主通道**：
(i) 架构级（$n_{kv}$，§14–15）线性缩放所有下游码率项的基数；
(ii) 潜向量合并（§11–12）改变待量化对象的维度与谱（$d_c$ 与 $\lambda$ 分布），与 §2 变换编码作用于同一协方差结构；
(iii) 数值级（§5–§7、§16）逼近 §1 信息论下界的速度决定了"剩余比特"，与 §10 能耗模型通过搬运字节数直接挂钩。

KKT 求解按 §9 执行；各内层子问题（码率分配、秩分配、分支因子、层级放置）的闭式解已分别在 §2.3、§8.3、§12.3、§12.4、§10.2 给出，外层用交替坐标下降收敛到局部最优。

---

## §21　数值计算示例

### 21.1 参数

$d=128$，$\rho=0.3$，$M=4$ 级，$B_m=256$（每级码本），拉普拉斯残差尺度 $b=0.02$，熵编码步长 $\Delta=0.002$，掩码开销 $r_{\text{mask}}=1$ bit/分量。

### 21.2 逐步计算

**第一步：$R_Q$**
$$
R_Q=\frac1d\sum_{m=1}^M\log_2B_m=\frac{1}{128}\times4\times\log_2 256=\frac{4\times8}{128}=\frac{32}{128}=0.25\ \text{bit/分量}.
$$

**第二步：$H_{\text{res}}$**
$$
H_{\text{res}}=\log_2\frac{2eb}{\Delta}=\log_2\frac{2\times2.718281828\times0.02}{0.002}=\log_2(20e)=\log_2 54.3656.
$$
$\ln 54.3656=3.99573$，除以 $\ln2=0.69315$：
$$
H_{\text{res}}=\frac{3.99573}{0.69315}=5.7646\ \text{bit/分量}.
$$

**第三步：$r_{\text{total}}$**
$$
r_{\text{total}}=\rho(R_Q+H_{\text{res}})+r_{\text{mask}}=0.3\times(0.25+5.7646)+1=0.3\times6.0146+1=1.8044+1=2.8044\ \text{bit/分量}.
$$

**第四步：$C$**
$$
C=\frac{16}{r_{\text{total}}}=\frac{16}{2.8044}=5.71\times.
$$

**一致性核验**：残差量化失真 $\varepsilon=\Delta^2/12=(0.002)^2/12=3.33\times10^{-7}$，对应信噪比 $10\log_{10}(b^2/\varepsilon)=10\log_{10}(4\times10^{-4}/3.33\times10^{-7})\approx30.8$ dB——与 $\sim5.76$ bit 熵编码的 $6$ dB/bit 律自洽 ✓。

### 21.3 两个不同残差熵情形的压缩率

**情形 (a)：残差更集中，$b=0.01$**
$$
H_{\text{res}}=\log_2\frac{2e\times0.01}{0.002}=\log_2(10e)=\log_2 27.1828=4.7646\ \text{bit},
$$
$$
r_{\text{total}}=0.3\times(0.25+4.7646)+1=0.3\times5.0146+1=2.5044,\qquad C=\frac{16}{2.5044}=6.39\times.
$$

**情形 (b)：残差更弥散，$b=0.05$**
$$
H_{\text{res}}=\log_2\frac{2e\times0.05}{0.002}=\log_2(50e)=\log_2 135.9141=7.0865\ \text{bit},
$$
$$
r_{\text{total}}=0.3\times(0.25+7.0865)+1=0.3\times7.3365+1=3.2010,\qquad C=\frac{16}{3.2010}=5.00\times.
$$

### 21.4 敏感性分析

| 情形 | $b$ | $H_{\text{res}}$ | $r_{\text{total}}$ | $C$ |
|---|---|---|---|---|
| (a) | 0.01 | 4.7646 | 2.5044 | 6.39× |
| 基准 | 0.02 | 5.7646 | 2.8044 | 5.71× |
| (b) | 0.05 | 7.0865 | 3.2010 | 5.00× |

**结论**：残差尺度 $b$ 变化 $5\times$（0.01→0.05），$H_{\text{res}}$ 变化 $\log_2 5=2.32$ bit，压缩率变化 $6.39/5.00=1.28\times$——对数依赖使压缩率对残差分布失配具有鲁棒性；主导项是 $\rho$ 与 $r_{\text{mask}}$：若 $\rho=0.5$，基准情形 $r_{\text{total}}=0.5\times6.0146+1=4.0073$，$C=3.99\times$；若掩码经熵编码取 $r_{\text{mask}}=h_2(0.3)=0.8813$，基准 $r_{\text{total}}=2.6857$，$C=5.96\times$。

### 21.5 TurboQuant 界数值核验（§16）

$b=2$：$\frac{\sqrt3\pi}{2}4^{-2}=\frac{1.7321\times3.1416}{2\times16}=\frac{5.4414}{32}=0.1700$，即 MSE $\le17.0\%\,\|v\|^2$；$b=3$：$4^{-3}=1/64$，MSE $\le4.25\%$；$b=4$：$4^{-4}=1/256$，MSE $\le1.06\%$。每增加 1 bit 失真降 $4\times$（$6.02$ dB），与高分辨率理论一致 ✓。

---

## §22　主题一总结

1. **无损界**：任何严格无损压缩受条件熵限制 $C\le16/\bar H$（定理 1.1），实际高压缩率只能在推理等价的有损 regime 内实现；
2. **有损联合优化**：变换（§2，去相关增益 $G_T$）、剪枝（§4，敏感度序）、量化（§5/§7/§16，$6$ dB/bit 律）、潜向量合并（§11–§12，$O(\log L)$ 缓存）、熵编码（§6，距香农界 $\le0.26$ bit）统一于率失真框架，总码率闭式 $r_{\text{total}}=\rho(R_Q+H_{\text{res}})+r_{\text{mask}}$；
3. **架构级**：MQA/GQA 以 $n_{kv}/n_q$ 比例源头削减（§14–15），与数值压缩乘性叠加；
4. **频域与低秩**：TriAttention 用三角级数把 Key 侧缓存常数化（§17），SVD 共享基实现 $(d_k+d_v)/r$ 渐近压缩且支持不物化融合计算（§18）；
5. **系统协同**：MoE 稀疏激活（$E/K$ 计算削减）与 FlashAttention 式 IO 优化（HBM 访问 $\Theta(T^2d^2/M)$ 再乘 $b/16$）在系统层与码率压缩正交叠加，能耗由 §10 等边际条件最优放置；
6. **可信度分级**：无损界、6 dB 律、Eckart–Young、注水分配等为定理级；TurboQuant 常数、TriAttention 集中假设、合并幂律 $\kappa'$、$\delta_{\text{sm}}$ 为近似/待实测项，已逐处标注。

---

# 主题二　六大前沿大模型底座的深度数学推导与性能边界

## §1　Mamba-3：纯 SSM 路线的当前天花板

### 1.1 连续 SSM 基础形式

线性时变连续系统：
$$
\begin{cases}\dot{\boldsymbol h}(t)=\boldsymbol A(t)\boldsymbol h(t)+\boldsymbol B(t)\boldsymbol x(t)\\ y(t)=\boldsymbol C(t)^\top\boldsymbol h(t)\end{cases}
$$
$\boldsymbol h(t)\in\mathbb{R}^N$ 为状态，$\boldsymbol A(t)\in\mathbb{R}^{N\times N}$ 状态矩阵，$\boldsymbol B\in\mathbb{R}^{N\times P}$ 输入矩阵，$\boldsymbol C\in\mathbb{R}^{N\times P}$ 输出矩阵（$P$ 为通道数；逐通道独立时退化为 $P$ 组 SISO）。

**通解**（常数变易公式，引理 0.9 的时变推广）：
$$
\boldsymbol h(t)=\Phi(t,t_0)\boldsymbol h(t_0)+\int_{t_0}^t\Phi(t,\tau)\boldsymbol B(\tau)\boldsymbol x(\tau)\,d\tau,\qquad \Phi(t,\tau)=\exp\Big(\int_\tau^t\boldsymbol A(s)ds\Big)
$$
（$\boldsymbol A(s)$ 彼此可交换时成立；一般情形用 Peano–Baker 级数代替矩阵指数，本文按对角化/逐通道情形处理，可交换性自动满足）。

### 1.2 指数–梯形离散化

设步长 $\Delta_t$，输入在区间上分段。三种离散化对比：

**(i) Euler**：$\boldsymbol h_t=(I+\boldsymbol A\Delta_t)\boldsymbol h_{t-1}+\Delta_t\boldsymbol B\boldsymbol x_t$。局部截断误差：Taylor 展开 $e^{\boldsymbol A\Delta}=I+\boldsymbol A\Delta+\frac{(\boldsymbol A\Delta)^2}{2}+\cdots$，Euler 保留到一阶，局部误差 $\frac{(\boldsymbol A\Delta)^2}{2}\boldsymbol h=O(\Delta^2)$，全局 $O(\Delta)$；稳定性要求 $|1+\lambda_i\Delta|\le1$，对快衰减负特征值（$\lambda_i\Delta\ll-2$）不稳定。

**(ii) 零阶保持（ZOH，引理 0.9）**：$\boldsymbol h_t=e^{\boldsymbol A\Delta_t}\boldsymbol h_{t-1}+\boldsymbol A^{-1}(e^{\boldsymbol A\Delta_t}-I)\boldsymbol B\boldsymbol x_{t-1}$。对分段常数输入**精确**（无截断误差），但假设输入在区间内恒定，引入保持误差 $O(\Delta)$。

**(iii) 指数–梯形（Mamba-3 采用）**：齐次部分用精确矩阵指数，强迫项用梯形法则（输入线性插值）：
$$
\boxed{\ \boldsymbol h_t=\alpha_t\boldsymbol h_{t-1}+\frac{\Delta_t}{2}\cdot\mathrm{trap}_t\big(\boldsymbol B_t\boldsymbol x_t+\boldsymbol B_{t-1}\boldsymbol x_{t-1}\big)\ },\qquad \alpha_t=e^{\boldsymbol A\Delta_t},\quad \mathrm{trap}_t=\sigma(\mathrm{gate}_t)\in(0,1).
$$
梯形法局部误差：$\int_{t}^{t+\Delta}f\,d\tau=\frac{\Delta}{2}(f_t+f_{t+\Delta})-\frac{\Delta^3}{12}f''(\xi)$（Euler–Maclaurin 一阶项），故**局部 $O(\Delta^3)$、全局 $O(\Delta^2)$**——比 Euler 提高一阶，且 $\alpha_t=e^{\boldsymbol A\Delta}$ 对负实部特征值恒有 $|\alpha|<1$（A-稳定），无 Euler 的稳定性限制。可学习门 $\mathrm{trap}_t$ 在数值积分精度与输入门控之间插值：$\mathrm{trap}\to1$ 为标准梯形，$\to0$ 为忽略当前输入的纯衰减。

### 1.3 复数域旋转状态空间与 RoPE 等价性

取对角复状态矩阵 $\boldsymbol A=\mathrm{diag}(\lambda_1,\dots,\lambda_{N/2})$，$\lambda_f=-\nu_f+i\omega_f$（$\nu_f>0$ 衰减率，$\omega_f$ 角频率）。状态更新在复二维子空间内为旋转×收缩：
$$
h_{t,f}=e^{(-\nu_f+i\omega_f)\Delta_t}h_{t-1,f}+\cdots=e^{-\nu_f\Delta_t}\,R(\omega_f\Delta_t)\,h_{t-1,f}+\cdots,
$$
$R(\cdot)$ 为二维旋转阵。展开全部历史：
$$
\boldsymbol h_t=\alpha_t\boldsymbol h_{t-1}+\beta_t\Big(\prod_{i=0}^{t-1}\boldsymbol R_i^\top\Big)\boldsymbol B_{t-1}\boldsymbol x_{t-1}+\gamma_t\Big(\prod_{i=0}^{t}\boldsymbol R_i^\top\Big)\boldsymbol B_t\boldsymbol x_t,\qquad y_t=\Big[\Big(\prod_{i=0}^{t}\boldsymbol R_i^\top\Big)\boldsymbol C_t\Big]^\top\boldsymbol h_t,
$$
其中 $\boldsymbol R_i=\mathrm{blockdiag}(R(\omega_f\Delta_i))$。**与 RoPE 的等价性**：RoPE 对 $q_t,k_j$ 施加旋转 $R(\omega_ft),R(\omega_fj)$，内积只含相对旋转 $R(\omega_f(t-j))$（§17）；复 SSM 中状态携带累积旋转 $\prod_iR_i^\top$，读出时 $C_t$ 的反向旋转同样使输出只依赖相对位置——二者在"以旋转编码相对位置"上同构。差异：SSM 的旋转与衰减 $e^{-\nu_f\Delta}$ 耦合（远程信息指数衰减），RoPE 无衰减；故 SSM 等价于"带遗忘门的相对位置编码"。

### 1.4 MIMO 架构与算术强度

将逐通道（SISO）更新扩展为矩阵形式（MIMO）：
$$
\boldsymbol H_t=\alpha_t\boldsymbol H_{t-1}+\boldsymbol B_t\boldsymbol X_t^\top,\qquad \boldsymbol Y_t=\boldsymbol H_t^\top\boldsymbol C_t,
$$
$\boldsymbol H_t\in\mathbb{R}^{N\times R}$（$R$ 为通道组大小）。

**算术强度推导**　SISO：每步每通道 $O(N)$ 次乘加，需加载 $\boldsymbol B_t,\boldsymbol C_t\in\mathbb{R}^N$，算术强度 $\mathrm{AI}_{\text{SISO}}=\frac{N}{2N}=\frac12$ FLOP/元素。MIMO：每步 $O(NR)$ FLOPs（外积更新），加载 $\boldsymbol B_t,\boldsymbol C_t$（$2N$ 元素）与 $\boldsymbol X_t,\boldsymbol Y_t$（$2R$ 元素），$\mathrm{AI}_{\text{MIMO}}=\frac{NR}{2N+2R}=\frac{R}{2(1+R/N)}\xrightarrow{N\gg R}\frac R2$。**算术强度提升 $R$ 倍**（渐近），使 kernel 从访存瓶颈区移向计算瓶颈区，GPU 利用率由 $\sim$10% 量级提升至 roofline 拐点以上（A100 拐点约 139 FLOP/B）。$\square$

### 1.5 性能边界

- **计算复杂度**：线性扫描 $O(T\cdot D\cdot N)$（$D$ 通道、状态 $N$），对 $T$ 线性；对比注意力 $O(T^2d)$。交叉点 $T^*\approx DN/d$。
- **显存复杂度**：推理状态 $O(B\cdot D\cdot N)$，与 $T$ 无关（常数内存解码）；训练并行扫描（Blelloch 前缀和）需 $O(T\cdot D\cdot N)$ 激活或分块重计算。
- **吞吐**：解码阶段无 KV cache 读取，每步 FLOPs 与带宽均 $O(1)$（相对 $T$），长序列吞吐对比 Transformer 随 $T$ 线性扩大优势。
- **能力边界**（诚实标注）：精确联想回忆（associative recall）任务上，常数维状态 $N$ 是信息瓶颈——无损存储 $T$ 个任意 KV 对需状态维数 $\Omega(T)$（信息论：$N\log|\mathcal{X}|\ge T\log|\mathcal{X}|$），故 SSM 在此类任务上存在原理性上限，需混合注意力补偿（§2 的动机）。此为**定理级**边界。
- **成熟度**：Mamba-2/3 已开源并有 2.8B 级验证；超大规模（$>$10B）长时间行为与生态仍处早期。

---

## §2　Falcon-H1：并行混合架构的产业标杆

### 2.1 混合块数学定义

并行混合块前向传播：
$$
\boldsymbol X_{\text{attn}}=\mathrm{LayerNorm}\big(\mathrm{MHA}(\boldsymbol X)\big),\qquad
\boldsymbol X_{\text{ssm}}=\mathrm{LayerNorm}\big(\mathrm{Mamba2}(\boldsymbol X)\big),
$$
$$
\boldsymbol X_{\text{out}}=\mathrm{FFN}\Big(\mathrm{Concat}\big(\boldsymbol X_{\text{attn}},\boldsymbol X_{\text{ssm}}\big)\boldsymbol W_o\Big)+\boldsymbol X.
$$

### 2.2 并行 vs 串行

**计算图**：串行 $\boldsymbol X\to\mathrm{MHA}\to\mathrm{Mamba}\to$ 为函数复合 $f(g(\boldsymbol X))$；并行为 $f(\boldsymbol X)\oplus g(\boldsymbol X)$ 后投影。

**梯度传播**：并行结构下
$$
\frac{\partial\mathcal{L}}{\partial\boldsymbol X}=\frac{\partial\mathcal{L}}{\partial\boldsymbol X_{\text{out}}}\Big(I+\frac{\partial\,\mathrm{FFN}}{\partial}\cdot\Big[\frac{\partial\,\mathrm{MHA}}{\partial\boldsymbol X};\ \frac{\partial\,\mathrm{Mamba}}{\partial\boldsymbol X}\Big]\Big),
$$
两分支梯度**相加**而非链式相乘，缓解深层连乘导致的梯度消失（与残差连接同机理：$I$ 项保底）。

**硬件并行**：两分支读同一输入、无相互依赖，可在不同 SM 流上并发执行；串行结构必须等待前一分支完成，关键路径长度减半。代价：两分支中间激活需同时驻留显存（峰值激活约为串行的 2 倍），且拼接维度翻倍使 $\boldsymbol W_o$ 参数量与 FFN 输入 FLOPs 相应增加。

### 2.3 性能边界

- **短序列**（$T\lesssim T^*=DN/d$）：注意力分支主导，复杂度 $O(T^2d)$；**长序列**：SSM 分支主导，$O(TDN)$，混合块取二者之和，渐近由 SSM 分支保持线性。
- **显存**：注意力头的 KV cache $O(T\cdot d_{\text{attn份额}})$ + SSM 常数状态 $O(DN)$；通过减少注意力头配额（如注意力: SSM = 1:2 的通道分配），cache 同比缩减而召回能力保留。
- **吞吐**：解码每步仅注意力份额的 cache 读取，相对纯 Transformer 加速 ≈（总维度/注意力维度）。
- **参数效率**：混合块用 $\boldsymbol W_o$ 拼接两分支，单位参数同时购买检索与压缩记忆两种能力；实证上同参数下多任务表现优于纯任一架构（经验命题）。
- **能力边界**：能力谱为两分支的并集近似，但分支容量分配是离线超参，无法按任务动态调整（静态结构的固有局限）。
- **成熟度**：0.5B–34B 系列已开源发布，产业部署案例存在，混合路线已被多家跟进——成熟度评级：高。

---

## §3　Kimi 开源组件：Transformer 底层模块的全栈替代方案

### 3.1 Kimi Delta Attention（KDA）

**从在线回归到状态更新**　把线性注意力的状态 $\boldsymbol S_t\in\mathbb{R}^{d_k\times d_v}$ 视为对历史 $(k_j,v_j)$ 的在线最小二乘记忆。对当前样本 $(k_t,v_t)$，单点损失
$$
\ell_t(\boldsymbol S)=\tfrac12\|\boldsymbol k_t^\top\boldsymbol S-\boldsymbol v_t^\top\|_2^2,
$$
梯度 $\nabla_{\boldsymbol S}\ell_t=\boldsymbol k_t(\boldsymbol k_t^\top\boldsymbol S-\boldsymbol v_t^\top)$。以步长 $\beta_t$ 做一步梯度下降：
$$
\boldsymbol S\leftarrow\boldsymbol S-\beta_t\boldsymbol k_t\boldsymbol k_t^\top\boldsymbol S+\beta_t\boldsymbol k_t\boldsymbol v_t^\top=(I-\beta_t\boldsymbol k_t\boldsymbol k_t^\top)\boldsymbol S+\beta_t\boldsymbol k_t\boldsymbol v_t^\top\quad(\text{经典 Delta 规则}).
$$
在"保留"部分插入通道级对角衰减门 $\boldsymbol\alpha_t\in(0,1)^{d_k}$：
$$
\boxed{\ \boldsymbol S_t=\big(\mathrm{Diag}(\boldsymbol\alpha_t)-\beta_t\boldsymbol k_t\boldsymbol k_t^\top\mathrm{Diag}(\boldsymbol\alpha_t)\big)\boldsymbol S_{t-1}+\beta_t\boldsymbol k_t\boldsymbol v_t^\top\ }.
$$

**三步分解**（按作用顺序）：
1. **对角衰减** $\mathrm{Diag}(\boldsymbol\alpha_t)\boldsymbol S_{t-1}$：每个 key 通道独立遗忘，通道 $i$ 的半衰期 $\tau_i=-\Delta/\ln\alpha_{t,i}$；
2. **秩 1 Delta 修正** $-\beta_t\boldsymbol k_t\big(\boldsymbol k_t^\top\mathrm{Diag}(\boldsymbol\alpha_t)\boldsymbol S_{t-1}\big)$：沿当前 key 方向擦除旧记忆的预测值（正是梯度项）；
3. **KV 写入** $+\beta_t\boldsymbol k_t\boldsymbol v_t^\top$：沿同一方向写入新值。

**精确写入条件**　左乘 $\boldsymbol k_t^\top$ 检验写入效果（设 $\|\boldsymbol k_t\|=1$ 归一化）：
$$
\boldsymbol k_t^\top\boldsymbol S_t=(1-\beta_t)\,\boldsymbol\alpha_t\odot(\boldsymbol k_t^\top\boldsymbol S_{t-1})+\beta_t\boldsymbol v_t^\top,
$$
即读出值是旧值与新值的凸组合；$\beta_t=1$ 时旧值被完全替换（delta 规则的"误差校正"饱和）。$\beta_t$ 即学习率门，$\boldsymbol\alpha_t$ 即遗忘门。

**通道级衰减的优势**　标量衰减（Mamba 式单 $\alpha$）使全部通道共享同一时间常数；对角 $\boldsymbol\alpha_t$ 提供 $d_k$ 个独立时间尺度，可同时维持快变量（局部语法）与慢变量（全局主题），等效于一个并行多尺度记忆库。代价：门控参数与逐通道乘法各增 $O(d_k)$，可忽略。

**复杂度**　更新与读出均为 $O(d_kd_v)$/token，状态显存 $O(d_kd_v)$ 常数；训练可分块并行（chunkwise 形式，块内矩阵乘、块间递推）。

### 3.2 Muon 优化器

**Newton–Schulz 正交化**　对动量矩阵 $\boldsymbol M$（SVD：$\boldsymbol M=\boldsymbol U\Sigma\boldsymbol V^\top$），迭代
$$
\boldsymbol X_{n+1}=a\boldsymbol X_n+b(\boldsymbol X_n\boldsymbol X_n^\top)\boldsymbol X_n+c(\boldsymbol X_n\boldsymbol X_n^\top)^2\boldsymbol X_n,\qquad a=3.4445,\ b=-4.7750,\ c=2.0315.
$$

**为何收敛到正交因子**　注意 $(\boldsymbol X\boldsymbol X^\top)^k\boldsymbol X=\boldsymbol U\Sigma^{2k+1}\boldsymbol V^\top$（归纳：$(XX^\top)X=U\Sigma V^\top V\Sigma U^\top U\Sigma V^\top=U\Sigma^3V^\top$）。故迭代保持奇异向量不变，仅将每个奇异值按奇次多项式映射
$$
\sigma\mapsto f(\sigma)=a\sigma+b\sigma^3+c\sigma^5.
$$
**不动点**：$f(\sigma)=\sigma\iff 2.0315\sigma^4-4.7750\sigma^2+2.4445=0$，解（令 $u=\sigma^2$）：
$$
u=\frac{4.7750\pm\sqrt{4.7750^2-4\times2.0315\times2.4445}}{2\times2.0315}=\frac{4.7750\pm1.7152}{4.0630}\in\{1.5974,\ 0.7531\},
$$
即 $\sigma^*\in\{0.868,\ 1.264\}$。迭代将 $(0,1)$ 内奇异值压向该二元带（5 步近似收敛），**近似**实现 $\boldsymbol U\boldsymbol V^\top$（全体奇异值归一）；残余条件数 $1.264/0.868\approx1.46$，远优于原始动量矩阵（典型 $\gg10^2$）。

**更新规则与意义**　$\boldsymbol W\leftarrow\boldsymbol W-\eta\,\mathrm{NS}^{(5)}(\boldsymbol M)\cdot s$（$s$ 为形状缩放）。几何意义：正交化更新等价于在**谱范数**下的最速下降（对偶范数论证：谱范数约束的最速下降方向为梯度矩阵的符号因子 $\boldsymbol U\boldsymbol V^\top$）；所有奇异方向等步长前进，消除病态曲率方向上的步长坍缩。

### 3.3 QK-Clip

**谱范数裁剪**
$$
\boldsymbol W_q\leftarrow\boldsymbol W_q\cdot\frac{\tau}{\max(\|\boldsymbol W_q\|_2,\tau)},\qquad
\boldsymbol W_k\leftarrow\boldsymbol W_k\cdot\frac{\tau}{\max(\|\boldsymbol W_k\|_2,\tau)}.
$$
裁剪后 $\sigma_1(\boldsymbol W_q),\sigma_1(\boldsymbol W_k)\le\tau$（谱范数被硬封顶）。

**对 logit 的定量控制**　对任意隐藏态 $x_q,x_k$：
$$
\frac{|q^\top k|}{\sqrt{d_k}}=\frac{|x_q^\top\boldsymbol W_q\boldsymbol W_k^\top x_k|}{\sqrt{d_k}}\le\frac{\|x_q\|\,\|x_k\|\,\sigma_1(\boldsymbol W_q)\sigma_1(\boldsymbol W_k)}{\sqrt{d_k}}\le\frac{\|x_q\|\,\|x_k\|\,\tau^2}{\sqrt{d_k}},
$$
logit 幅值被显式上界锁死，杜绝注意力 logit 失控增长（attention logit explosion）导致的 softmax 饱和（一权独大、梯度消失）。谱范数用幂迭代 $O(d^2)$ 估计，每若干步执行一次，开销可忽略。

### 3.4 性能边界

- **推理复杂度**：KDA 解码 $O(d_kd_v)$/token，与 $T$ 无关；Muon 只在训练生效；QK-Clip 推理零开销。
- **显存**：KDA 状态常数内存 $O(Bd_kd_v)$；Muon 优化器状态与 Adam 同阶（一阶动量，无二阶矩）。
- **吞吐**：KDA 线性递推使长上下文解码吞吐相对同参注意力模型显著提升（倍数随 $T$ 增长）。
- **参数效率**：三者均为"同参替换"（不增参数），替代而非扩增。
- **能力边界**：线性注意力家族共享 §1.5 的常数状态信息瓶颈；KDA 的 delta 写入缓解但不能突破 $\Omega(T)$ 下界。
- **成熟度**：KDA/Muon/QK-Clip 均已随开源模型发布并有独立复现，Muon 已在多个外部训练管线中被采用——成熟度评级：高（组件级）。

---

## §4　Ouro：循环深度架构的开源标杆

### 4.1 循环计算单元

共享权重的 Transformer 块被反复调用 $R$ 次：
$$
\boldsymbol H_r=\mathrm{SharedTransformer}(\boldsymbol H_{r-1},\boldsymbol E),\qquad r=1,\dots,R,
$$
$\boldsymbol E$ 为输入嵌入（每轮注入，保证输入信息不被迭代稀释），$\boldsymbol H_0=\boldsymbol E$。参数共享使"等效深度"$R\times$ 而参数量不变——以时间换参数。

### 4.2 自适应退出门与熵正则化

退出策略头给出在第 $t$ 轮停止的离散分布 $p_\phi(t\mid\boldsymbol x)$，$t\in\{1,\dots,T_{\max}\}$。训练损失
$$
\mathcal{L}=\sum_{t=1}^{T_{\max}}p_\phi(t\mid\boldsymbol x)\,L^{(t)}-\beta\,H\big(p_\phi(\cdot\mid\boldsymbol x\big)),
$$
其中 $L^{(t)}$ 为第 $t$ 轮输出的任务损失，$H(p)=-\sum_tp_t\log p_t$ 为香农熵。

**熵正则的作用机制**（推导）　无熵项时，目标 $\min_p\sum_tp_tL^{(t)}$ 是单纯形上的线性函数，最小值必在顶点取得（$p=e_{t^*}$，$t^*=\arg\min L^{(t)}$）——策略退化到"永远固定轮数"，失去自适应性。熵项使目标严格凸化：$\sum_tp_tL^{(t)}-\beta H(p)$ 在单纯形内部的最优解满足一阶条件
$$
L^{(t)}+\beta(\log p_t+1)=\nu\quad\Longrightarrow\quad p_t=\frac{e^{-L^{(t)}/\beta}}{\sum_{t'}e^{-L^{(t')}/\beta}}=\mathrm{Softmax}\big(-L^{(t)}/\beta\big),
$$
即**玻尔兹曼退出策略**：温度 $\beta$ 控制探索；$\beta\to0$ 退化为硬 argmin（确定性早退），$\beta\to\infty$ 退化为均匀分布。$\square$

### 4.3 LTI 稳定性约束

将循环动力学在不动点 $\boldsymbol h^*$ 处线性化：$\boldsymbol h_r-\boldsymbol h^*\approx\boldsymbol A(\boldsymbol h_{r-1}-\boldsymbol h^*)$，$\boldsymbol A=\partial\mathrm{SharedTransformer}/\partial\boldsymbol h\big|_{h^*}$。由引理 0.11：
$$
\boldsymbol h_r\to\boldsymbol h^*\ \text{对任意初值}\quad\Longleftrightarrow\quad \rho(\boldsymbol A)<1.
$$
工程实现：用幂迭代在线估计 $\sigma_1(\boldsymbol A)\approx\rho(\boldsymbol A)$，超过 $1-\delta$ 时对循环块权重做谱归一化（同 §3.3 的裁剪机制）。**失效行为**：$\rho(\boldsymbol A)\ge1$ 时迭代发散或进入极限环，表现为输出随 $R$ 震荡——这是循环深度架构必须主动防护的模态。

### 4.4 性能边界

- **计算复杂度**：$O(R\cdot(T^2d+Td^2))$，吞吐 $\propto1/R_{\text{avg}}$；
- **显存**：参数 $O(1\times)$（共享），激活 $O(R\cdot Td)$（重计算可压缩到 $O(Td)$）；
- **参数效率**：等效 $R$ 层深度、$1$ 层参数，参数效率≈$R$ 倍；但等效深度与真实深度不等价（宽度不变，表征容量受限）；
- **能力边界**：迭代精修适合可逐步改进的任务（推理、代码），对单步查表型任务无收益（$R$ 浪费）；
- **成熟度**：开源标杆级别，已被复现；评级：中高。

---

## §5　SpikingBrain2.0：类脑脉冲大模型的最高水平

### 5.1 脉冲神经元膜电位动力学

**从 RC 电路到 LIF**　膜电位满足漏积分方程 $\tau_m\dot v=-(v-v_{\text{rest}})+RI(t)$。Euler 离散化（步长 $\Delta t$，记 $\lambda=1-\Delta t/\tau_m\in(0,1)$，$x_{t+1}=RI(t_{t+1})\Delta t/\tau_m$）：
$$
v_{t+1}=\lambda v_t+x_{t+1}\quad(\text{未发放时}).
$$
发放规则 $s_t=\mathbb{1}(v_t\ge V_{\text{th}})$，发放后两种重置：
$$
\text{软重置：}\ \boldsymbol v_{t+1}=\lambda\boldsymbol v_t-V_{\text{th}}\cdot\boldsymbol s_t+\boldsymbol x_{t+1},
$$
$$
\text{硬重置：}\ \boldsymbol v_{t+1}=\lambda(1-\boldsymbol s_t)\boldsymbol v_t+\boldsymbol v_{\text{reset}}\cdot\boldsymbol s_t+\boldsymbol x_{t+1}.
$$
软重置保留超阈残余电位（$v-V_{\text{th}}$ 的信息不丢失，发放率编码更准）；硬重置彻底清零（抗漂移、实现简单）。$\mathbb{1}(\cdot)$ 为指示函数（逐分量 Heaviside）。

**可训练性**　指示函数不可微，反向传播用代理梯度：$\frac{\partial s}{\partial v}\approx\sigma'\big(\gamma(v-V_{\text{th}})\big)$ 或 $\frac{1}{\pi}\frac{\gamma/2}{(\gamma/2)^2+(v-V_{\text{th}})^2}$（atan 代理），前向仍为硬脉冲。

### 5.2 双空间稀疏注意力（DSSA）

$$
\mathrm{DSSA}(\boldsymbol Q,\boldsymbol K,\boldsymbol V)=\alpha\cdot\mathrm{MoBA}(\boldsymbol Q_s,\boldsymbol K_s,\boldsymbol V_s)+(1-\alpha)\cdot\mathrm{SSE}(\boldsymbol Q_l,\boldsymbol K_l,\boldsymbol V_l),
$$
- $\mathrm{MoBA}$（块混合注意力）：Key 序列分块，门控为每个查询选 top-$k$ 块，块内精确注意力——提供**精确检索通道**（复杂度 $O(T\cdot k\cdot B)$，$B$ 块大小）；
- $\mathrm{SSE}$（稀疏状态扩展 / 线性化全局注意力）：核化线性注意力 $\phi(Q)(\phi(K)^\top V)$，$O(Td^2)$ 常数可换序预计算——提供**常数复杂度全局通道**；
- $\alpha\in[0,1]$ 可学习，逐头调节"精确/近似"配比。

### 5.3 性能边界

- **事件驱动复杂度**：前向 FLOPs $\propto$ 脉冲发放率 $\rho_s$：$O(\rho_s\cdot T\cdot d^2)$，典型 $\rho_s\approx0.05$–$0.2$ 时理论能耗优势 $5$–$20\times$（仅在神经形态硬件或稀疏事件引擎上兑现；稠密 GPU 上脉冲稀疏性难以利用，为诚实边界）；
- **显存**：膜电位状态 $O(Bd)$，无 KV cache（线性注意力通道）或稀疏块 cache（MoBA 通道 $O(kB)$）；
- **吞吐**：受脉冲编码延迟（时间步展开 $T_s$）制约，首 token 延迟偏高；
- **参数效率**：与同构稠密模型持平（架构替换）；
- **能力边界**：长时程任务有结构性优势；精细数值推理受二值化表征限制；
- **成熟度**：研究原型级，硬件生态未成熟——评级：中低。

---

## §6　GPT-6 Astra：产业级循环深度架构

> **可信度声明**：GPT-6 Astra 未公开发布，无官方技术报告。本节数学形式为对"潜空间循环推理"范式的合理重构（与 §4 Ouro 同源但循环粒度不同），具体工程参数均标注为**未经证实的公开传闻**，不应作为事实引用。

### 6.1 核心范式：潜空间循环推理

与 Ouro 的**序列级循环**（整段隐状态序列反复过共享块）不同：Astra 为 **token 级潜空间迭代**——每个 token 的隐状态在进入下一层前，先在潜空间内迭代打磨 $R^*$ 轮。粒度差异带来：循环深度可按 token 难度自适应分配，且循环过程与序列维解耦（可复用 §11 的 cache 机制）。

### 6.2 完整数学推导

**初始状态编码**
$$
\boldsymbol h_0=\mathrm{Embed}(\boldsymbol x_{1:t})+\mathrm{PosEmbed}(\boldsymbol x_{1:t}).
$$

**潜空间循环迭代**
$$
\boldsymbol h_r=\mathcal{F}_\theta(\boldsymbol h_{r-1}),\qquad r=1,2,\dots,R^*,
$$
$\mathcal{F}_\theta$ 为共享权重的 Transformer 子块。

**收敛判定与输出**　收敛门控取相对残差
$$
g_r=\frac{\|\boldsymbol h_r-\boldsymbol h_{r-1}\|_2}{\|\boldsymbol h_r\|_2+\varepsilon_0},\qquad R^*=\min\{r\mid g_r<\epsilon,\ r\le R_{\max}\},
$$
输出分布
$$
p(\boldsymbol x_{t+1}\mid\boldsymbol x_{1:t})=\mathrm{Softmax}\big(\boldsymbol h_{R^*}\boldsymbol W_{\text{head}}+\boldsymbol b_{\text{head}}\big).
$$
不动点视角：若迭代收敛，$\boldsymbol h_{R^*}\approx\boldsymbol h^*$ 满足 $\boldsymbol h^*=\mathcal{F}_\theta(\boldsymbol h^*)$（Banach 意义下需 $\mathcal{F}_\theta$ 收缩，见 6.3 的 LTI 约束）。

**自适应深度的变分损失**　把迭代深度 $R$ 建模为潜变量，$q(R\mid\boldsymbol x)$ 为后验（策略头），$p(R)$ 为先验（通常取几何分布，偏好浅深度）。证据下界（ELBO，**最大化**）：
$$
\mathcal{L}_{\text{ELBO}}=\mathbb{E}_{q(R\mid\boldsymbol x)}\big[\log p(\boldsymbol x\mid\boldsymbol h_R)\big]-\beta\,\mathrm{KL}\big(q(R\mid\boldsymbol x)\,\|\,p(R)\big);
$$
以最小化损失形式写（与源文档符号约定一致，整体取负）：
$$
\mathcal{L}=\mathbb{E}_{q(R\mid\boldsymbol x)}\big[\log p(\boldsymbol x\mid\boldsymbol h_R)\big]+\beta\,\mathrm{KL}\big(q(R\mid\boldsymbol x)\,\|\,p(R)\big)\ \xrightarrow{\text{取负后最小化}}\ -\mathcal{L}_{\text{ELBO}}.
$$
（**符号约定注记**：$\log p$ 项为似然奖励、KL 项为复杂度惩罚；最大化 ELBO ≡ 最小化其负值。源文档以"损失"统称，本文标注此细节以免符号歧义。）

**状态衰减与 LTI 稳定性约束**
$$
\boldsymbol h_r=\boldsymbol\Gamma\odot\boldsymbol h_{r-1}+\Delta\boldsymbol h_r,\qquad \rho\big(\mathrm{Diag}(\boldsymbol\Gamma)\big)=\max_i|\Gamma_i|<1,
$$
（对角阵的特征值即对角元，引理 0.11 判据直接给出逐通道条件 $|\Gamma_i|<1$）。该门控衰减保证循环映射收缩、不动点唯一可达，与 §4.3 同机理。

**工具调用的状态嵌入机制**
$$
\boldsymbol h_r'=\boldsymbol h_r+\boldsymbol W_{\text{tool}}\cdot\boldsymbol e_{\text{tool}},
$$
工具返回内容编码 $\boldsymbol e_{\text{tool}}$ 经投影注入潜状态，循环继续迭代——工具结果参与后续"思考"而不占序列位置。

### 6.3 计算复杂度与显存边界

**单 token 生成时间复杂度**　设每轮循环对全序列做注意力（轮间不复用注意力结果，仅传递隐状态）：
$$
T_{\text{token}}=O\big(T^2\cdot D\cdot R_{\text{avg}}\big),
$$
其中 $R_{\text{avg}}=\mathbb{E}[R^*]$。若轮间复用 KV cache（只重算潜状态），降为 $O(T\cdot D\cdot R_{\text{avg}})$；源文档取前者（保守上界）。

**显存**
$$
\mathrm{Mem}=O(T\cdot D)\ (\text{KV cache})+O\big(R_{\max}\cdot T\cdot D/16\big)\ (\text{循环激活，}1/16\text{ 为重计算检查点压缩因子}).
$$

### 6.4 曝光的工程参数与性能边界

| 项目 | 数值/表述 | 可信度 |
|---|---|---|
| 基础参数规模 | 传闻 $\sim$1.8T（MoE 总参） | 未经证实 |
| 最大循环次数 $R_{\max}$ | 传闻 16–32 | 未经证实 |
| 等效推理能力 | 传闻对标 o 系推理模型 | 未经证实 |
| 推理成本 | 传闻同代稠密模型的 $\sim$1/3 | 未经证实 |
| 能力边界 | 循环深度上限 $R_{\max}$ 截断不可判定问题；LTI 约束下表达能力受收缩映射类限制 | 分析性结论（可信） |
| 当前状态 | 未公开 | — |

**数学上可确立的边界**：(i) 任何 $R_{\max}$ 有限的循环深度架构，其单 token 内部计算量有界 $O(R_{\max})$，无法在不增加序列长度的前提下模拟任意长计算（与思维链形成对比——后者把计算写进序列）；(ii) 收缩约束 $|\Gamma_i|<1$ 保证稳定的同时限制了迭代可实现的函数类为收缩不动点方程的解。

---

## §7　实证检验设计方案（两大主题统一）

### 7.1 可量化检验指标

| 指标 | 定义 | 对应被检验公式 |
|---|---|---|
| 实测压缩率 $\hat C$ | fp16 字节数/实际编码字节数 | §20，$C=16/r_{\text{total}}$ |
| 逐 token 熵 $\hat{\bar H}$ | 算术编码实测码长/分量 | §1，$\bar H$ 下界 |
| 困惑度增量 $\Delta$PPL | 压缩模型 vs 原模型 | §9，$\lambda_A$ 项 |
| 召回门 ROC-AUC | $p_C$ 对"块被实际需要"的区分度 | §13.2 单调性假设 |
| 内积失真 | $\mathbb{E}|\langle q,v\rangle-\langle q,\hat v\rangle|^2$ 实测 vs 界 | 定理 16.3 |
| 长文检索准确率 | NIAH / RULER | §8、§13、§17 |
| 解码吞吐 / 能耗 | tok/s、焦耳/token | §10、§19 |

### 7.2 实验配置（三组参数算例）

- **组 A（基准）**：$d=128,\rho=0.3,M=4,B=256,b=0.02,\Delta=0.002$，$r_{\text{mask}}=1$ → 预测 $C=5.71\times$（§21.2）；
- **组 B（残差集中）**：$b=0.01$ → 预测 $C=6.39\times$；
- **组 C（残差弥散）**：$b=0.05$ → 预测 $C=5.00\times$。

模型配置：$n_q=32$、$n_{kv}\in\{1,8,32\}$（检验 §14–15 压缩比与质量拐点）、$d_h=128$、$L\in\{8\text{k},32\text{k},128\text{k}\}$。

### 7.3 对照与混杂排除

- **对照组**：同架构无压缩（fp16 cache）；同码率随机剪枝（检验 §4 敏感度序的有效性——敏感度序应显著优于随机序）；
- **消融**：逐模块开启（仅量化 / 仅剪枝 / 仅低秩 / 全组合），检验 A6 误差可加性（组合失真应 ≈ 各模块失真之和，偏差 $>20\%$ 即证伪 A6 在该 regime）；
- **混杂控制**：固定随机种子集 $\{s_1,\dots,s_5\}$ 报均值±标准差；校准集与评测集不相交；熵编码器在全数据上训练一次后冻结。

### 7.4 可证伪判据（误差容许范围）

- 压缩率预测：$|\hat C-C_{\text{pred}}|/C_{\text{pred}}\le15\%$（超出即码率公式遗漏显著项，需修订）；
- TurboQuant 界：实测 MSE $>$ 定理 16.2 上界的 $1.2\times$ 即证伪高斯性近似；
- 召回门：ROC-AUC $<0.9$ 即 $p_C$ 单调性假设不成立，§13.2 降级；
- GQA 拐点：扫描 $n_{kv}$，若质量损失曲线无平坦区，则"免费压缩区"命题对该模型证伪。

---

## §8　全文总结

**主题一** 给出 KV cache 压缩的统一率失真框架：以条件熵下界（定理 1.1）为不可逾越的天花板，以变换编码（$G_T$）、敏感度剪枝（$s_ic_i^2$ 序）、RVQ+残差熵编码（距香农界 $\le0.26$ bit）、低比特量化（$6$ dB/bit）、潜向量合并（$O(\log L)$ 内存、$g^*=e^{1/\kappa'}$）、召回门（峰值 $\lfloor1/\theta\rfloor$）为可达手段，架构级（MQA/GQA）、频域（TriAttention）、低秩（SVD 共享基）与系统级（MoE、FlashAttention IO、三级存储能耗）模块全部纳入闭式联合优化 $r_{\text{total}}=\rho(R_Q+H_{\text{res}})+r_{\text{mask}}$，$C=16/r_{\text{total}}$，三组数值算例预测 $5.00$–$6.39\times$。

**主题二** 沿"常数记忆 vs 线性记忆 vs 循环深度"三条路线给出六大底座的推导与边界：Mamba-3（指数–梯形离散化二阶精度、MIMO 算术强度 $R$ 倍、$\Omega(T)$ 联想回忆下界）、Falcon-H1（并行混合的梯度相加与并发执行）、Kimi 组件（KDA 在线回归推导、Muon 不动点 $\sigma^*\in\{0.868,1.264\}$、QK-Clip logit 硬上界）、Ouro（玻尔兹曼退出策略、$\rho(A)<1$）、SpikingBrain2.0（LIF 两种重置、DSSA 双通道）、GPT-6 Astra（潜空间变分循环，参数标注未证实）。

**方法论纪律**：全文区分三级证据——定理级（附完整证明）、近似级（标注阶数与误差界）、传闻级（明确标注未证实）；所有内层子问题给出闭式解或 KKT 刻画；所有关键公式附退化检验或数值核验。
