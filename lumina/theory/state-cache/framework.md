# 深度神经网络表征坍缩统一理论

> 从精确秩亏判定到任意阶低秩压缩的定律级闭合框架  
> 权威排版稿：[framework.tex](framework.tex) · [framework.pdf](framework.pdf)（本文件为同结构可读副本；冲突时以 tex 为准）  
> 目录：`lumina/theory/state-cache/`  
> 日期：2026-09-05

**三级串联**：L0 精确秩亏判定 → L1 深度表示坍缩 → L2 训练动力学秩坍缩。

证据分级约定：【I】定理级（完整证明）；【II】近似级（标注阶数与误差界）；【III】经验/边界（需实测或外延）。

---

## 摘要

深度网络训练与推断中的表征退化集中表现为权重谱与表示谱的低秩化，但「精确零奇异值」的判定、层复合下的坍缩来源与训练过程中的谱收缩长期分散于三个互不衔接的理论体系。本文以精确秩亏判定为公理基底，构建三级串联的闭合数学框架：

- **（L0）** 在谱隙 $\gamma$ 与扰动界 $\|E\|_2\le\varepsilon$ 下，阈值法精确恢复秩的充要条件为 $\gamma>2\varepsilon$，并给出数值容差定律 $\gamma>2\varepsilon+2\eta_{\mathrm{alg}}\|A\|_2$；
- **（L1）** 线性复合的秩单调坍缩与瓶颈饱和（Sylvester 秩界），并以 ReLU 秩增反例精确标定非线性适用边界；
- **（L2）** 核范数软阈值收缩（SVT）闭合解与 0 级退化临界时间闭合公式 $\sigma_i(t)=\max(\sigma_i(0)-\lambda t,\,0)$。

三级由同一公共阈值 $\tau$ 串联，统一为「从 0 级完全退化到任意阶低秩压缩」的闭合失真公式
$$
D(k(\tau))=\sum_{i>k(\tau)}\sigma_i^2.
$$
全部 8 条引理与 8 条定理/推论附完整证明；配套纯标准库、固定种子（$\mathrm{SEED}=20240904$）、三层（精确算例 E / 蒙特卡洛 MC / 真实数据契约）可证伪核验器，判据 F1–F7 实测零违例，其中精确恢复判据在 5000 次随机谱隙试验中判定正确率 $5000/5000$。

**关键词**：表征坍缩；精确秩亏；谱隙；奇异值阈值；核范数；低秩压缩

---

## 1. 引言

低秩化是深度神经网络中跨结构普遍出现的现象：深度线性网络的学习动力学对低秩解具有系统偏好；过参数化的深度矩阵分解在梯度流下隐式地趋向低秩与谱压缩。这些观察共同指向一个谱几何事实——网络的权重谱与表示谱在训练与复合过程中被持续压低，部分奇异值可被精确压至零。

本文所论的**表征坍缩**指谱意义下的秩退化：矩阵的若干奇异值为**精确零**（0 级退化）或尾谱被压缩（$k$ 阶低秩化）。它与终局训练阶段的分类器几何「Neural Collapse」（类均值向单纯形等角紧框架收敛）是不同层面的现象：后者刻画类间几何，本文刻画谱秩结构。

围绕这一现象，三个基础问题长期分散在互不衔接的文献中：

1. **判定问题**——仅凭观测矩阵与扰动界，秩亏能否被精确判定？矩阵扰动论给出 Weyl 逐点界与 Mirsky $\ell_2$ 界，但未与「精确零」的 0/1 判定闭合；
2. **来源问题**——层复合中坍缩由谁承载？Sylvester 秩不等式给出线性界的雏形，而激活非线性的作用缺乏精确标定；
3. **演化问题**——训练中谱如何收缩？核范数正则的近端映射（SVT）给出一步闭式，但其与判定、压缩的公共参数化缺失。

本文以第一性原理从精确秩亏判定出发（公理 A0–A5），构建三级串联的定律级闭合体系，贡献为：

1. **L0 判定定律**（定理 1–2）：谱隙 $\gamma>2\varepsilon$ 是阈值法精确恢复秩的充要条件，并给出 $\gamma=2\varepsilon$ 的统一失效边界与数值容差定律 $\gamma>2\varepsilon+2\eta_{\mathrm{alg}}\|A\|_2$；
2. **L1 坍缩定律**（定理 3–4，命题 1）：深度表示坍缩由线性秩亏严格承载（秩单调帽与瓶颈饱和），并以 ReLU 秩增反例（$\mathrm{rank}\,1\to 2$）精确标定非线性边界；
3. **L2 演化定律**（定理 5–6）：核范数软阈值收缩闭合解与 0 级退化临界时间闭合公式 $T_i=\sigma_i(0)/\lambda$；
4. **统一闭合**（定理 7）：三级由公共阈值 $\tau$ 串联为「判定–收缩–压缩」一体的闭合失真公式；全部结论附可证伪判据 F1–F7 与纯标准库核验器（见 [framework.tex](framework.tex) 附录），实测零违例。

全文组织：§2 公理系统；§3 预备引理；§4 三级主定理与统一闭合；§5 边界条件、极限与算例；§6 数值核验；§7 实证检验方案；§8 讨论与结论。

---

## 2. 公理系统与元理论

### 2.1 基本对象与退化层级

**定义 1（层矩阵与谱）**　设 $A\in\mathbb{R}^{m\times n}$ 为任意一层的权重矩阵、特征矩阵或内容矩阵（统称**层矩阵**）。其奇异值分解（SVD）为
$$
A=U\,\Sigma\,V^\top,\qquad
\Sigma=\mathrm{diag}(\sigma_1,\dots,\sigma_p),\quad p=\min(m,n),\quad
\sigma_1\ge\sigma_2\ge\cdots\ge\sigma_p\ge0,
$$
$\sigma_i(A)$ 记第 $i$ 大奇异值，谱（多重集）记为 $\sigma(A)=\{\sigma_i\}_{i=1}^{p}$。

**定义 2（精确秩、0 级退化阶与谱隙）**
- **精确秩** $r=\mathrm{rank}(A):=\#\{i:\sigma_i(A)>0\}$；
- **0 级退化阶**（精确秩亏）$\nu_0(A):=p-\mathrm{rank}(A)=\#\{i:\sigma_i(A)=0\}$；
- $k$ 阶（近似）低秩残差 $\tau_k(A):=\sum_{i>k}\sigma_i^2(A)$；
- **谱隙** $\gamma_r(A):=\sigma_r-\sigma_{r+1}$（约定 $\sigma_{p+1}:=0$）。当 $\mathrm{rank}(A)=r$ 时 $\sigma_{r+1}=0$，故 $\gamma_r=\sigma_r$，下文简记 $\gamma$。

**注（「0 级」语义）**　「0 级退化」专指谱中的**精确零**（$\sigma_i=0$），即秩亏的 0/1 判定，与「$k$ 阶近似低秩」（小而非零的尾谱）严格区分。二者由公共阈值 $\tau$（§4.4）串联：$\sigma_i<\tau$ 经软阈值收缩被**精确置零**，从而把 $k$ 阶逼近转化为精确 $k$-秩，形成统一闭合。

### 2.2 公理 A0–A5

- **A0（论域与度量）**　研究对象为实层矩阵 $A\in\mathbb{R}^{m\times n}$ 及其 SVD 谱；退化现象唯一由谱多重集 $\sigma(A)$ 度量；度量范数为 Frobenius 范数 $\|\cdot\|_F$ 与谱范数 $\|\cdot\|_2$。
- **A1（谱可计算）**　给定 $A$，其奇异值可在算法相对精度 $\eta_{\mathrm{alg}}$ 内计算：$|\hat\sigma_i-\sigma_i|\le\eta_{\mathrm{alg}}\,\|A\|_2$。本框架采用单侧 Jacobi 方法，其奇异值具有满相对精度 $\eta_{\mathrm{alg}}\approx u$（$u$ 为机器舍入单位）。
- **A2（观测扰动）**　实际观测 $\hat A=A+E$，扰动 $E$ 谱范数有界 $\|E\|_2\le\varepsilon$（确定型），或二阶矩有界 $\mathbb{E}\,\|E\|_2^2\le\varepsilon^2$（随机型）。判定知识仅来自 $\hat A$ 与界 $\varepsilon$。
- **A3（层复合结构）**　表示经层映射 $X_{\ell+1}=\phi(X_\ell W_\ell)$ 逐层演化，其中 $W_\ell$ 为层权重，激活 $\phi$ 逐元素、$L$-Lipschitz 且 $\phi(0)=0$（覆盖 ReLU、GeLU、$\tanh$；不含平移激活）。
- **A4（谱损失训练动力学）**　权重演化服从（子）梯度流或一步近端映射，目标为**谱线性损失**
  $$
  \Psi(W)=\lambda\,\|W\|_*+\tfrac12\|W-X\|_F^2,\qquad \|W\|_*=\sum_i\sigma_i(W),
  $$
  即核范数正则的最小二乘（近端映射目标）。
- **A5（数值精度有限）**　浮点舍入单位为 $u$（双精度 $u=2^{-53}$）；0 级判定阈值须满足 $\tau>\eta_{\mathrm{alg}}\,\|A\|_2$，否则零奇异值的数值噪声（量级 $\eta_{\mathrm{alg}}\,\|A\|_2$）将被误判为退化。

### 2.3 相容性与独立性【I】

**定理（相容性）**　公理 A0–A5 相容：对角谱模型 $A_0=\mathrm{diag}(3,2,1,0,0)\in\mathbb{R}^{5\times5}$ 同时满足 A0–A5。

*证明*　A0：$A_0$ 有良定义 SVD，$\sigma(A_0)=\{3,2,1,0,0\}$。A1：对角阵的谱可精确读出（取 $\eta_{\mathrm{alg}}=0$，或双精度下单侧 Jacobi 给 $\eta_{\mathrm{alg}}\approx u$）。A2：任取 $\varepsilon\in(0,1/2)$ 作扰动界自洽。A3：取 $\phi=\mathrm{ReLU}$（$\phi(0)=0$、$1$-Lipschitz）与 $W=I$。A4：$\Psi(W)=\frac12\|W-X\|_F^2+\lambda\|W\|_*$ 在 $X=A_0$ 处良定义且凸。A5：双精度下 $\tau$ 可取 $0.5>\eta_{\mathrm{alg}}\|A_0\|_2$。五条同时成立，故相容。$\square$

**定理（独立性）**　A0 为语言层元公理；A1–A5 各自存在满足其余公理而违反该条的反例，故相互独立：

| 反例 | 破坏 | 构造要点 |
|---|---|---|
| 破 A1 | 谱不可精确计算 | 仅含舍入误差 $u$ 的低精度子程序估计谱并宣称「无零奇异值」，判定失去意义 |
| 破 A2 | 扰动无界 | $E$ 的谱范数无先验界 $\varepsilon$，任何判定无从给出 |
| 破 A3 | 平移激活破坏 $0$ 保持 | 取 $\phi=\mathrm{sigmoid}$（$\phi(0)=1/2\neq0$），层复合脱离本文论域 |
| 破 A4 | 非谱损失 | 取 $\Psi$ 为逐坐标鲁棒损失，SVT 闭合解不再成立 |
| 破 A5 | 无限精度 | 理想实数无限精度机器上 $\tau$ 可任意小，数值容差定律失效 |

每个反例仅破坏指定公理，其余公理不受影响，故 A1–A5 互不蕴含。$\square$

---

## 3. 预备引理【I】

后续所有定理仅引用这些引理与公理，构成封闭证明链。

### 引理 1（秩–零度）

对 $A\in\mathbb{R}^{m\times n}$：$\mathrm{rank}(A)+\dim\mathrm{null}(A)=n$，其中 $\mathrm{null}(A)=\{x:Ax=0\}$。

*证明*　对 $A$ 施 Gauss 消元化为行阶梯形：主元列数 $=\mathrm{rank}(A)$，自由列数 $=n-\mathrm{rank}(A)$，而每个自由变量张成零空间的一个自由维度，故 $\dim\mathrm{null}(A)=n-\mathrm{rank}(A)$。$\square$

### 引理 2（Sylvester 秩界）

对 $A\in\mathbb{R}^{m\times k}$、$B\in\mathbb{R}^{k\times n}$：$\mathrm{rank}(AB)\le\min\{\mathrm{rank}(A),\mathrm{rank}(B)\}$。

*证明*　(i) $\mathrm{col}(AB)\subseteq\mathrm{col}(A)$，故 $\mathrm{rank}(AB)\le\mathrm{rank}(A)$。(ii) $Bx=0\Rightarrow ABx=0$，故 $\mathrm{null}(B)\subseteq\mathrm{null}(AB)$，$\dim\mathrm{null}(B)\le\dim\mathrm{null}(AB)$；由引理 1，$\mathrm{rank}(B)=n-\dim\mathrm{null}(B)$，故 $\mathrm{rank}(B)\ge n-\dim\mathrm{null}(AB)=\mathrm{rank}(AB)$。两不等式取 $\min$ 即得。$\square$

### 引理 3（秩亏计数）

$\mathrm{rank}(XW)=\mathrm{rank}(W)-\dim\big(\mathrm{null}(X)\cap\mathrm{col}(W)\big)$。

*证明*　视 $X$ 为限制在 $\mathrm{col}(W)$ 上的线性映射 $X|_{\mathrm{col}(W)}:\mathrm{col}(W)\to\mathrm{col}(XW)$。对该映射用秩–零度（引理 1）：$\dim\mathrm{col}(XW)=\dim\mathrm{col}(W)-\dim\mathrm{null}(X|_{\mathrm{col}(W)})$，且 $\mathrm{null}(X|_{\mathrm{col}(W)})=\mathrm{null}(X)\cap\mathrm{col}(W)$；左端即 $\mathrm{rank}(XW)$。$\square$

### 引理 4（奇异值极小极大刻画，Courant–Fischer）

$$
\sigma_i(A)=\max_{\dim S=i}\ \min_{\substack{x\in S\\ x\neq0}}\frac{\|Ax\|_2}{\|x\|_2}.
$$

*证明*　设 $A=U\Sigma V^\top$，$v_1,\dots,v_p$ 为 $V$ 的列。**下界**：取 $S=\mathrm{span}\{v_1,\dots,v_i\}$，对 $x=\sum_{j\le i}\alpha_jv_j$ 有 $\|Ax\|^2=\sum_{j\le i}\sigma_j^2\alpha_j^2\ge\sigma_i^2\|x\|^2$，故该 $S$ 上的最小比值 $\ge\sigma_i$。**上界**：对任意 $\dim S=i$ 的子空间，由维数公式 $\dim\big(S\cap\mathrm{span}\{v_i,\dots,v_p\}\big)\ge i+(p-i+1)-p=1$，取其中非零 $x$，则 $\|Ax\|^2=\sum_{j\ge i}\sigma_j^2\alpha_j^2\le\sigma_i^2\|x\|^2$，故最小比值 $\le\sigma_i$。两者结合得 max–min 恰为 $\sigma_i$。$\square$

### 引理 5（Weyl 奇异值扰动不等式）

对 $A,B\in\mathbb{R}^{m\times n}$：

1. $|\sigma_i(A+B)-\sigma_i(A)|\le\|B\|_2=\sigma_1(B)$ 对一切 $1\le i\le p$ 成立；
2. $\sigma_{i+j-1}(A+B)\le\sigma_i(A)+\sigma_j(B)$，约定 $\sigma_l=0\ (l>p)$。

*证明*　(i) 由引理 4 与三角不等式：对任意 $\dim S=i$ 与 $x\in S$，$\|(A+B)x\|\le\|Ax\|+\|B\|_2\|x\|$，故 $\sigma_i(A+B)\le\sigma_i(A)+\|B\|_2$；交换 $A$ 与 $A+B$ 的角色得反向不等式。(ii) 记 $E_1$ 为 $A+B$ 的前 $i+j-1$ 个右奇异向量张成的子空间，$N_A=\mathrm{span}\{v_i^{A},\dots,v_p^{A}\}$，$N_B=\mathrm{span}\{v_j^{B},\dots,v_p^{B}\}$。由维数公式 $\dim(E_1\cap N_A\cap N_B)\ge1$，取其中非零 $x$：一方面 $x\in E_1$ 给出 $\sigma_{i+j-1}(A+B)\le\|(A+B)x\|/\|x\|$；另一方面 $x\in N_A\cap N_B$ 给出 $\|(A+B)x\|\le(\sigma_i(A)+\sigma_j(B))\|x\|$。两者结合即 (ii)。$\square$

### 引理 6（Mirsky 不等式）

$\big(\sum_i|\sigma_i(A+E)-\sigma_i(A)|^2\big)^{1/2}\le\|E\|_F$。

*证明*　构造对称膨胀 $M_A=\begin{pmatrix}0&A^\top\\ A&0\end{pmatrix}$，其特征值恰为 $\pm\sigma_1(A),\dots,\pm\sigma_p(A)$ 及 $m+n-2p$ 个零；且 $M_{A+E}=M_A+M_E$，$\|M_E\|_F^2=2\|E\|_F^2$。对 Hermitian 阵的 Hoffman–Wielandt 不等式给出（按降序配对）
$$
2\sum_i\big(\sigma_i(A+E)-\sigma_i(A)\big)^2
=\sum_{l=1}^{m+n}\big(\lambda_l(M_{A+E})-\lambda_l(M_A)\big)^2
\le\|M_E\|_F^2=2\|E\|_F^2.
$$
两端除以 $2$ 即得。$\square$

### 引理 7（Eckart–Young–Mirsky）

$\displaystyle\min_{\mathrm{rank}(B)\le k}\ \|A-B\|_F^2=\sum_{i>k}\sigma_i^2(A)$，极值点为截断 SVD $B=\sum_{i\le k}\sigma_iu_iv_i^\top$。

*证明*　**下界**：对任意 $\mathrm{rank}(B)\le k$，令 $C=A-B$，则 $\sigma_{k+1}(B)=0$。由引理 5(ii)（取指标 $i=k+1$，$j=q$）：$\sigma_{k+q}(A)=\sigma_{(k+1)+q-1}(B+C)\le\sigma_{k+1}(B)+\sigma_q(C)=\sigma_q(C)$。平方求和：$\|C\|_F^2=\sum_{q\ge1}\sigma_q^2(C)\ge\sum_{q\ge1}\sigma_{k+q}^2(A)=\sum_{i>k}\sigma_i^2(A)$。**达到**：$B=\sum_{i\le k}\sigma_iu_iv_i^\top$ 时 $A-B=\sum_{i>k}\sigma_iu_iv_i^\top$ 各项两两正交，$\|A-B\|_F^2=\sum_{i>k}\sigma_i^2$。$\square$

### 引理 8（逐元素映射的 Hadamard 分解）

若 $\phi$ 逐元素且 $\phi(0)=0$，则存在逐元素函数 $h$（$h(0)=\phi'(0)$，或按极限定义）使 $\phi(Z)=Z\odot H$，$H_{ij}=h(Z_{ij})$；若 $\phi$ 另为 $L$-Lipschitz，则 $|h(z)|\le L$。

*证明*　定义 $h(z)=\phi(z)/z\ (z\neq0)$，$h(0)=\phi'(0)$（存在时；否则取极限值）。由 $\phi(0)=0$，逐元素 $\phi(Z_{ij})=Z_{ij}\,h(Z_{ij})$，即 $\phi(Z)=Z\odot H$。Lipschitz 性：$|h(z)|=|\phi(z)|/|z|\le L\,|z|/|z|=L\ (z\neq0)$。$\square$

---

## 4. 主要结果：三级串联与统一闭合

### 4.1 Level 0：精确秩亏判决定律

**定理 1（0 级退化判定 / 谱隙定律）【I】**　设 $A$ 精确秩 $r=\mathrm{rank}(A)$，谱隙 $\gamma:=\sigma_r(A)>0$ 且 $\sigma_{r+1}(A)=0$。观测 $\hat A=A+E$，$\|E\|_2\le\varepsilon$。定义阈值判定 $\hat r_\tau:=\#\{i:\hat\sigma_i(\hat A)\ge\tau\}$。则：

1. **秩不降**：若 $\varepsilon<\gamma$，则 $\sigma_r(\hat A)\ge\gamma-\varepsilon>0$，故 $\mathrm{rank}(\hat A)\ge r$；
2. **精确恢复**：若 $\gamma>2\varepsilon$，则任取 $\tau\in(\varepsilon,\ \gamma-\varepsilon]$，有 $\hat r_\tau=r$ 精确成立；
3. **失效标定**：存在 $E_0=-\gamma\,u_rv_r^\top$（$u_rv_r^\top$ 为 $\sigma_r$ 对应的秩-1 单位项）使 $\|E_0\|_2=\gamma$ 且 $\mathrm{rank}(A+E_0)=r-1$；故 $\varepsilon\ge\gamma$ 时秩可降。

*证明*　(a) 由引理 5(i)，$i\le r$ 时 $\hat\sigma_i\ge\sigma_i(A)-\|E\|_2\ge\gamma-\varepsilon$；$\varepsilon<\gamma$ 给出前 $r$ 个奇异值严格为正，故 $\mathrm{rank}(\hat A)\ge r$。(b) 对 $i>r$：$\sigma_i(A)=0$，引理 5(i) 给 $\hat\sigma_i\le\|E\|_2\le\varepsilon<\tau$；对 $i\le r$：$\hat\sigma_i\ge\gamma-\varepsilon\ge\tau$。故 $\#\{\hat\sigma_i\ge\tau\}=r$。(c) $A=\sum_{i\le r}\sigma_iu_iv_i^\top$，而 $A+E_0=\sum_{i<r}\sigma_iu_iv_i^\top$ 秩恰为 $r-1$，且 $\|E_0\|_2=\gamma$。$\square$

**推论 1（统一失效边界）【I】**　阈值法的可判定性由 $\gamma=2\varepsilon$ 划分：

| 区间 | 结论 |
|---|---|
| $\gamma>2\varepsilon$ | 精确可判（分离区间 $(\varepsilon,\gamma-\varepsilon]$ 非空） |
| $\varepsilon<\gamma\le2\varepsilon$ | 秩不降但分离阈值不存在（区间为空） |
| $\gamma\le\varepsilon$ | 存在使秩下降的容许扰动（定理 1(c)） |

*证明*　分离区间非空当且仅当 $\varepsilon<\gamma-\varepsilon$，即 $\gamma>2\varepsilon$；其余两段分别由定理 1(a) 与 (c) 给出。$\square$

**定理 2（数值容差定律）【I】**　在 A1 的算法误差与 A5 的机器误差下，0 级判定可靠当且仅当
$$
\gamma>2\varepsilon+2\,\eta_{\mathrm{alg}}\,\|A\|_2,
$$
其中右端第二项为满相对精度谱估计算法（单侧 Jacobi）的零奇异值噪声上界。

*证明*　由 A1 与 A2 的叠加（三角不等式），观测谱的真误差被 $\varepsilon+\eta_{\mathrm{alg}}\|A\|_2$ 控制；将其代入定理 1(b) 的分离条件 $\gamma>2(\varepsilon+\eta_{\mathrm{alg}}\|A\|_2)$ 即得。若改用 Gram 法（$A^\top A$）则条件数被平方，零奇异值噪声升至 $O(\sqrt{u})\,\|A\|_2$，数值容差定律即被破坏。$\square$

### 4.2 Level 1：深度表示坍缩

**定理 3（线性复合秩单调坍缩）【I】**　对线性层链 $X_{\ell+1}=X_\ell W_\ell$（A3 退化为 $\phi=\mathrm{id}$），
$$
\mathrm{rank}(X_L)\le\min\Big\{\mathrm{rank}(X_1),\ \min_{1\le\ell<L}\mathrm{rank}(W_\ell)\Big\}.
$$

*证明*　$\ell=1$：由引理 2，$\mathrm{rank}(X_2)\le\min\{\mathrm{rank}(X_1),\mathrm{rank}(W_1)\}$。归纳：设 $\mathrm{rank}(X_\ell)\le B_\ell:=\min\{\mathrm{rank}(X_1),\mathrm{rank}(W_1),\dots,\mathrm{rank}(W_{\ell-1})\}$，则 $\mathrm{rank}(X_{\ell+1})\le\min\{\mathrm{rank}(X_\ell),\mathrm{rank}(W_\ell)\}\le B_{\ell+1}$。归纳至 $L$ 得证。$\square$

**推论 2（瓶颈饱和）【I】**　任意单层权重的秩亏 $b$（$\mathrm{rank}(W_\ell)=b$）使**全部下游**表示的秩被帽于 $b$；特别地，若某权重精确秩亏 $b<\mathrm{rank}(X_1)$，则深层表示发生线性链内**不可逆**的 $b$ 维坍缩。

*证明*　定理 3 中 $\min_\ell\mathrm{rank}(W_\ell)\le b$ 即对一切 $\ell'>\ell$ 施加 $\mathrm{rank}(X_{\ell'})\le b$；下游线性复合不增秩，故坍缩不可逆。$\square$

**推论 3（单层坍缩的精确计数）【I】**　线性层 $XW$ 相较 $W$ 的秩亏恰为 $\dim(\mathrm{null}(X)\cap\mathrm{col}(W))$：
$$
\mathrm{rank}(XW)=\mathrm{rank}(W)-\dim\big(\mathrm{null}(X)\cap\mathrm{col}(W)\big).
$$
其几何含义：$W$ 的列空间中与 $X$ 零空间重合的部分被逐层消灭，构成表示坍缩的**单一矢量级原因**。

*证明*　即引理 3。$\square$

**命题 1（非线性可增秩——坍缩定律的适用边界）【I】**　逐元素 $\phi$（$\phi(0)=0$）一般**不保持**秩单调：存在 $Z$ 使 $\mathrm{rank}(\mathrm{ReLU}(Z))>\mathrm{rank}(Z)$。故定理 3 的秩单调是**线性**层专有结论，非线性 $\phi$ 可部分解除秩亏。

*证明*　取
$$
Z=\begin{pmatrix}1&-1\\-1&1\end{pmatrix},\qquad
\mathrm{ReLU}(Z)=\begin{pmatrix}1&0\\0&1\end{pmatrix},
$$
$Z$ 的两列互为相反向量，故 $\mathrm{rank}(Z)=1$，而 $\mathrm{rank}(\mathrm{ReLU}(Z))=2>1$。该构造与引理 8 一致：$Z\odot H$ 的秩不受 $\mathrm{rank}(Z)$ 约束。核验判据 F5 精确复现 $1\to2$。$\square$

**注（坍缩的准确来源定位）**　深度网络的**表示坍缩**由**线性秩亏**（窄瓶颈、低秩投影）严格承载（推论 2–3）；非线性激活只可能在下游**部分恢复**秩（命题 1），却不能解除上游已施加的线性秩帽。此定位消解了「非线性可坍缩/可增秩」的表观矛盾。

### 4.3 Level 2：训练动力学秩坍缩

**定理 4（SVT 软阈值收缩闭合解）【I】**　核范数正则问题（A4）
$$
\min_{W}\ \tfrac12\|W-X\|_F^2+\lambda\|W\|_*
$$
的唯一解为奇异值阈值算子
$$
\mathrm{SVT}_\lambda(X)=U\,\mathrm{diag}\!\big(\max(\Sigma-\lambda I,0)\big)\,V^\top,
\qquad \Sigma=\mathrm{diag}(\sigma_1,\dots,\sigma_p),
$$
其中 $\max$ 逐元素作用于对角线；且 $\sigma_i(X)\le\lambda\Rightarrow\sigma_i(\mathrm{SVT}_\lambda(X))=0$（精确置零）。

*证明*　由 von Neumann 迹不等式，对任意 $W$：$\langle W,X\rangle\le\sum_i\sigma_i(W)\sigma_i(X)$，等号当且仅当 $W$ 与 $X$ 共享有序左右奇异向量。展开 $\frac12\|W-X\|_F^2=\frac12\|W\|_F^2-\langle W,X\rangle+\frac12\|X\|_F^2$，记 $s_i=\sigma_i(W)$、$x_i=\sigma_i(X)$，目标泛函下界为
$$
\sum_i\Big[\tfrac12 s_i^2-(x_i-\lambda)s_i\Big]+\tfrac12\|X\|_F^2.
$$
对每个 $s_i\ge0$ 逐分量最小化（严格凸）：$s_i^*=\max(x_i-\lambda,0)$。取 $W^*=\mathrm{SVT}_\lambda(X)$：它与 $X$ 共享奇异向量，von Neumann 不等式取等，故下界被达到；又 $\frac12\|W-X\|_F^2$ 严格凸，最小化子唯一。置零性质由 $s_i^*=0\iff x_i\le\lambda$ 立得。$\square$

**定理 5（0 级退化临界时间闭合公式）【I】**　在核范数子梯度流 $\dot W\in-\lambda\,\partial\|W\|_*$ 下（A4 的连续极限），奇异值沿独立闭式演化
$$
\sigma_i(t)=\max\big(\sigma_i(0)-\lambda t,\ 0\big),
$$
故 $\sigma_i$ 在**有限**时间 $T_i=\sigma_i(0)/\lambda$ 达到 0 级退化（$\sigma_i=0$），且
$$
\mathrm{rank}\big(W(t)\big)=\#\{i:\sigma_i(0)>\lambda t\}.
$$

*证明*　核范数的次微分具有谱分解结构 $\partial\|W\|_*=\{UV^\top+Q:\ U^\top Q=0,\ QV=0,\ \|Q\|_2\le1\}$。在 $\sigma_i>0$ 的时段内秩局部常值，奇异值可微且满足 $\dot\sigma_i=u_i^\top\dot Wv_i$。代入 $\dot W=-\lambda G$、$G=UV^\top+Q\in\partial\|W\|_*$：$u_i^\top(UV^\top)v_i=1$，而 $u_i^\top Qv_i=0$，故 $\dot\sigma_i=-\lambda$。当 $\sigma_i$ 触零后，谱函数次微分在零坐标上的投影为区间 $[-1,1]$，轨道可冻结。综上奇异值轨道满足标量微分包含 $\dot\sigma_i\in-\lambda\,\partial|\sigma_i|$，由标量比较原理其唯一绝对连续解为 $\sigma_i(t)=\max(\sigma_i(0)-\lambda t,0)$；令 $\sigma_i(t)=0$ 得 $T_i=\sigma_i(0)/\lambda$。核验判据 F7 以独立 Euler 积分复核该闭式。$\square$

**定理 6（梯度步的秩演化上界）【I】**　对单步梯度下降 $W_{t+1}=W_t-\eta g_t$：$\mathrm{rank}(W_{t+1})\le\mathrm{rank}(W_t)+\mathrm{rank}(g_t)$。

*证明*　列空间满足 $\mathrm{col}(A+B)\subseteq\mathrm{col}(A)+\mathrm{col}(B)$，故秩次可加：$\mathrm{rank}(A+B)\le\mathrm{rank}(A)+\mathrm{rank}(B)$。代入 $A=W_t$、$B=-\eta g_t$。$\square$

**注（三级由阈值 $\tau$ 串联）**　定理 1 的判定阈值 $\tau$ 与定理 4 的收缩参数 $\lambda$ 是同一标量：L0 用它**判定**哪些 $\sigma_i$ 为 0 级退化（$<\tau$ 视为零），L2 用它**精确置零**（$\sigma_i<\lambda$ 收缩至 0）。取 $\tau=\lambda$ 后，$k(\tau):=\#\{\sigma_i\ge\tau\}$ 同时是判定秩、收缩秩与低秩压缩秩。

### 4.4 统一闭合公式

**定理 7（0 级退化 $\to$ 任意阶低秩压缩的统一闭合）【I】**　设谱 $\sigma_1\ge\cdots\ge\sigma_p\ge0$，取公共阈值 $\tau>0$，令 $k(\tau):=\#\{\sigma_i\ge\tau\}$。则以下三式由同一 $\tau$ 闭合：

$$
\boxed{\ \text{(L0 判定)}\quad
\nu_0=\#\{\sigma_i<\tau\}=p-k(\tau),
\qquad\text{可判}\iff\gamma>2\varepsilon\ }
$$

$$
\boxed{\ \text{(L2 收缩)}\quad
\mathrm{SVT}_\tau(W)=U\,\mathrm{diag}\!\big(\max(\Sigma-\tau I,0)\big)V^\top,
\qquad \mathrm{rank}(\mathrm{SVT}_\tau)=k(\tau)\ }
$$

$$
\boxed{\ \text{(任意阶压缩)}\quad
D(k(\tau))=\min_{\mathrm{rank}(B)\le k(\tau)}\|W-B\|_F^2
=\sum_{i>k(\tau)}\sigma_i^2\ }
$$

*证明*　第一式为定理 1 与定义 2 的直接组合；第二式为定理 4（$\lambda=\tau$）；第三式为引理 7。三者共享同一 $k(\tau)$，故闭合。$\square$

---

## 5. 边界条件、极限与算例

### 5.1 极限与失效条件标定

| 极限 | 行为 | 状态 |
|---|---|---|
| $\tau\to0^{+}$ | $k(\tau)\to\mathrm{rank}(A)$，判定退化为「无容差」极限 | 数值上违背 A5，**失效** |
| $\tau\to\sigma_1^{+}$ | $k(\tau)\to0$，全谱判定为退化，$\mathrm{SVT}_\tau(W)\to0$，$D(0)\to\|W\|_F^2$ | 边界 |
| $\gamma\to0^{+}$ | 分离区间对任何固定 $\varepsilon>0$ 为空 | 精确判定失效；仅能给 $k$ 阶逼近 |
| $\lambda\to0$ | $\mathrm{SVT}_\lambda\to W$（无收缩） | 退化为纯低秩逼近 |
| $\lambda\to\infty$ | $\mathrm{SVT}_\lambda\to0$（完全退化），$k(\lambda)\to0$ | 边界 |
| 完全退化（$r=0$） | $\mathrm{rank}(W)=0\iff W=0$；$D(0)=\|W\|_F^2$ | 闭合 |

### 5.2 自洽性验算

1. **零阈值还原**：$\tau=0$ 时判定还原精确秩 $r$，SVT 还原 $W$ 本身，压缩残差还原 $0$。
2. **软/硬阈值一致性**：$\lambda=\tau$ 时 SVT 的核范数收缩与 Eckart–Young 硬阈值截断在**秩**上一致（$\mathrm{rank}(\mathrm{SVT}_\tau)=k(\tau)$），在**谱值**上相差软/硬阈值；前 $k$ 个分量的失真之差恰为 $\sum_{i\le k}\min(\sigma_i,\tau)^2$，可解析给出。
3. **L0–L1 相容**：判定秩 $r$ 与深度线性坍缩秩 $\mathrm{rank}(X_L)\le r$ 相容（推论 2）。

### 5.3 数值算例（全代入）

**算例 1（谱隙判定）**　$A=\mathrm{diag}(3,2,1,0,0)$（$r=3$，$\gamma=1$），扰动 $E=\delta I$（$\|E\|_2=\delta$）。取 $\delta=0.3<\gamma/2=0.5$，分离区间 $(0.3,\,0.7]$ 内取 $\tau^*=\gamma/2=0.5$：观测谱 $\hat\sigma=(3.3,2.3,1.3,0.3,0.3)$，$\#\{\hat\sigma\ge0.5\}=3=r$ 精确恢复。失效反例 $E_0=-\gamma u_3v_3^\top$ 使第三奇异值归零，谱 $(3,2,0,0,0)$、秩 $2=r-1$。核验 F1 以 $\delta\in\{0.1,0.3,0.49\}$ 全部通过。

**算例 2（线性坍缩与非线性边界）**　$X\in\mathbb{R}^{7\times3}$（$\mathrm{rank}=3$）、$W\in\mathbb{R}^{3\times6}$（$\mathrm{rank}=3$）$\Rightarrow\mathrm{rank}(XW)=3\le\min(3,3)$（Sylvester 界紧）。ReLU 反例 $\mathrm{rank}(Z)=1\to\mathrm{rank}(\mathrm{ReLU}(Z))=2$。核验 F4 零违例、F5 精确复现 $1\to2$。

**算例 3（SVT 收缩与临界时间）**　$\sigma=(3,2,1,0.5)$，$\lambda=0.75$：SVT 后 $\hat\sigma=(2.25,1.25,0.25,0)$，$\mathrm{rank}=3=\#\{\sigma_i>0.75\}$；$\sigma_4=0.5$ 的退化临界时间 $T_4=0.5/0.75=0.666667$。核验 F6 秩/谱闭合值零违例，F7 退化时间与独立 Euler 积分一致（最大偏差 $2.02\times10^{-12}$）。

---

## 6. 数值核验

### 6.1 核验器设计

核验器 `verify-degeneration.py`（完整源码见 [framework.tex](framework.tex) 附录 A）遵循四项设计原则：

1. **判据先行**：每条定理对应可证伪判据 F1–F7，带数值阈值与方向，失败即输出 FAIL 并保留现场数字；
2. **零依赖**：纯 Python 标准库；SVD 采用单侧 Jacobi 列正交化，奇异值具有满相对精度（误差 $\sim u\,\sigma_1$，不平方条件数），满足 A1 与定理 2；
3. **三层结构**：E 层（小规模精确算例，秒级，默认运行）；MC 层（`--mc` 大样本蒙特卡洛证伪）；DATA 层（`--data` 真实数据契约 `degeneration-v1`）；
4. **确定性**：固定种子 $\mathrm{SEED}=20240904$，全部输出打印并落盘。

### 6.2 判据 F1–F7 实测结果

（$\mathrm{SEED}=20240904$，2026-09-04 执行；科学计数保留两位有效数字。）

| 判据 | 内容（阈值方向） | E 层（精确算例） | MC 层（大样本） |
|---|---|---|---|
| F1 谱隙判决 | $\delta<\gamma/2$ 全恢复；$\delta\ge\gamma$ 秩降 | $\delta\in\{0.1,0.3,0.49\}$ 全恢复 $r{=}3$；反例秩 $2$ | $5000/5000$ 正确 |
| F2 Eckart–Young | $\lvert\text{残差}-\sum_{i>k}\sigma_i^2\rvert<10^{-9}$ | $k{=}1/3/5$：$0,\ 8.88\times10^{-16},\ 0$ | $800$ 组最大 $9.95\times10^{-14}$ |
| F3 Weyl/Mirsky | 超额 $\le0$；$\ell_2$ 违例数 $=0$ | Weyl $-7.37\times10^{-2}$，Mirsky $-2.26\times10^{-1}$，违例 $0$ | $-1.68\times10^{-2}$，$-8.44\times10^{-2}$，违例 $0$ |
| F4 Sylvester 秩界 | $\mathrm{rank}(XW)>\min$ 计数 $=0$ | $1000$ 组违例 $0$ | $1000$ 组违例 $0$ |
| F5 ReLU 秩增 | $\mathrm{rank}\,1\to2$ 复现 | $1\to2$ 复现 | （精确反例，非随机） |
| F6 SVT 闭合解 | 秩违例 $0$；谱偏差 $<10^{-9}$ | $1000$ 组违例 $0$，谱偏差 $0$ | 违例 $0$，谱偏差 $0$ |
| F7 退化临界时间 | 闭式 vs Euler 偏差 $<10^{-6}$ | $t{=}0.5/2.0$：$8.74\times10^{-13},\ 2.02\times10^{-12}$；$T=0.666667$ | （闭式对照，独立积分） |

E 层结论为**全部判据通过**（退出码 $0$）；MC 层全部判据**零违例**。

### 6.3 工程质量门禁

单元测试 `test_verify_degeneration.py` 共 $21$ 例全部通过，覆盖三层：内核（SVD 重构、谱、数值秩、谱范数、SVT 闭式秩与谱）、判据端到端（F1–F7 复算与 E 层总出口）、数据契约（模板自校验、format 缺失、矩阵维度非法、秩字段非法）。静态检查：`mypy --strict` 零类型错误；`ruff` 零 lint 违例；复杂度审计全部函数圈复杂度 $\le9$（门限 $10$）、嵌套 $\le3$（门限 $4$）。

---

## 7. 实证检验方案

### 7.1 量化检验指标

1. **判定准确率**（F1）：$P[\hat r_\tau=r\mid\gamma>2\varepsilon]$，期望 $=1$；对照 $\gamma\le2\varepsilon$ 区间的判定失败率。
2. **压缩残差偏差**（F2）：$\big|\|W-\hat W_k\|_F^2-\sum_{i>k}\sigma_i^2\big|/\sum_{i>k}\sigma_i^2$，阈值 $<10^{-9}$。
3. **扰动不等式余量**（F3）：$\max_i\big(|\sigma_i(A{+}E)-\sigma_i(A)|-\|E\|_2\big)$，符号须 $\le0$；并计 $\ell_2$ 违例数。
4. **秩界违例数**（F4）：$\#\{\mathrm{rank}(XW)>\min(\mathrm{rank}\,X,\mathrm{rank}\,W)\}$，期望 $0$。
5. **收缩闭合值偏差**（F6）：$\|\hat\sigma-\max(\sigma-\lambda,0)\|_\infty$，阈值 $<10^{-9}$。
6. **退化时间闭合误差**（F7）：$\max_i|\sigma_i(t)-\max(\sigma_i(0)-\lambda t,0)|$，Euler 对照，阈值 $<10^{-6}$。

### 7.2 实验步骤与数据处理

合成谱由固定种子 $\mathrm{SEED}=20240904$ 生成；扰动 $E$ 取秩-1 单位张量 $\delta\,uv^\top$（$\|E\|_2=\delta$ 可控）或各向同性 $\delta I$；SVD 用单侧 Jacobi（不平方条件数）；秩判定用相对容差 $\eta_{\mathrm{alg}}\sigma_1$；MC 大样本层以违例计数与最大超额为汇总统计量。真实数据入口 `--data` 采用契约 `degeneration-v1`。

### 7.3 对照设计

1. **上/下半区间对照**：$\delta<\gamma/2$（应全对）对 $\delta=\gamma$（应秩降），F1 内部分列。
2. **算法精度对照**：单侧 Jacobi 对 Gram 法（$A^\top A$ 平方条件数，零奇异值噪声 $O(\sqrt{u})\|A\|_2$）；后者违反数值容差定律，被明确排除。
3. **非线性阴性对照**：ReLU 秩增反例（F5）作为坍缩定律适用边界的阴性对照。

### 7.4 可证伪判定标准

任一判据满足即**证伪**对应定理：

- (F1) 存在 $\delta<\gamma/2$ 且 $\tau\in(\delta,\gamma-\delta]$ 使 $\hat r_\tau\neq r$；
- (F2) 残差偏差 $\ge10^{-9}$；
- (F3) 存在 $i$ 使 $|\sigma_i(A{+}E)-\sigma_i(A)|>\|E\|_2+10^{-9}$；
- (F4) 存在 $\mathrm{rank}(XW)>\min(\mathrm{rank}\,X,\mathrm{rank}\,W)$；
- (F6) 收缩谱值偏差 $\ge10^{-9}$；
- (F7) 闭式与 Euler 偏差 $\ge10^{-6}$。

全部判据实测零违例，故本框架在其公理域内未被证伪（截至 2026-09-04，$\mathrm{SEED}=20240904$）。

---

## 8. 讨论与结论

### 8.1 适用范围（充分必要条件）

本理论适用于：谱可精确或高精度计算（$\eta_{\mathrm{alg}}\|A\|_2$ 远小于谱隙）、扰动有界（$\varepsilon$ 已知）、且训练目标为谱线性（核范数正则）的矩阵退化判定。

- L0 判定定律与 L1 线性坍缩定律为无近似的精确结论；
- SVT 收缩在 A4 谱损失下为精确闭合；
- 训练动力学结论（定理 5）在 A4 之外不具普适性。

### 8.2 假设边界与未建模项

1. **L1 非线性**：秩单调坍缩是线性层结论；非线性 $\phi$ 可增秩，故「任意激活下表示秩单调不增」**不成立**——本框架将坍缩准确定位到线性秩亏。
2. **L2 动力学普适性**：定理 5 假定 A4；对一般非谱损失训练动力学（如交叉熵加 SGD 噪声与自适应优化器），秩演化无普适闭式。
3. **数值容差**：0 级判定以 $\eta_{\mathrm{alg}}\|A\|_2$ 为下限；真实零与「小但非零」在 $\tau$ 以下不可分辨，此为 A5 的**原理性**边界。
4. **维度有限**：全部结论限于 $p=\min(m,n)$ 有限；$m,n\to\infty$ 的随机矩阵渐近谱（Marchenko–Pastur 律）不在本框架内。
5. **与 Neural Collapse 的关系**：本文刻画谱秩结构的坍缩与压缩，与终局训练的分类器几何现象分属不同层面；谱隙判据可为后者提供表征谱端的互补诊断量。

### 8.3 结论

本框架把「深度网络表征退化」从经验观察收敛为一条**可判定、可收缩、可压缩**的闭合链：

- 0 级退化由谱隙与扰动之比精确判定（$\gamma>2\varepsilon$，含数值容差修正）；
- 表示坍缩由线性秩亏精确承载（单调秩帽与单一矢量级原因）；
- 训练坍缩由核范数软阈值精确收缩（闭合解与有限临界时间 $T_i=\sigma_i(0)/\lambda$）；
- 三者由公共阈值 $\tau$ 串联为统一失真公式 $D(k(\tau))=\sum_{i>k(\tau)}\sigma_i^2$。

全套结论附完整证明链、定量误差上界、失效条件与可证伪判据，由固定种子核验器逐项复核，实测零违例。

后续方向：随机矩阵渐近谱的外延、非谱损失下秩动力学的可控松弛、以及真实训练管线的在线谱监测。

### 8.4 数据与代码可用性

核验器完整源码逐字节嵌入 [framework.tex](framework.tex) 附录 A，亦可作为独立文件 `verify-degeneration.py` 运行（纯 Python 标准库，无第三方依赖）；单元测试（21 例）随 `test_verify_degeneration.py` 提供。

**利益冲突声明**：作者声明不存在利益冲突。

---

## 附录 A：数据契约 `degeneration-v1` 与复现命令

### A.1 契约模板

```json
{
  "format": "degeneration-v1",
  "source": {"name": "示例", "note": "离线矩阵交接（或仅谱）"},
  "records": [
    {"m": 4, "n": 4,
     "matrix": [[3.0, 0, 0, 0], [0, 2.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 0.0]],
     "truncation_ranks": [1, 2]}
  ]
}
```

字段语义：

| 字段 | 约束 |
|---|---|
| `format` | 必填，恒为 `degeneration-v1` |
| `records` | 必填，非空数组 |
| `records[i].m` / `n` | 正整数维度 |
| `records[i].matrix` | $m\times n$ 有限数值矩阵，必填 |
| `records[i].truncation_ranks` | 可选，$0\le r<\min(m,n)$ 整数数组 |
| `records[i].source.name` | 可选命名 |

维度上限 $128\times128$（超限提示走谱路径）。核验输出：数值秩 $r$、谱隙 $\gamma$、0 级退化数、尾谱 $\sum_{i>r}\sigma_i^2$ 与各截断秩的最优残差。

### A.2 复现命令

```bash
python verify-degeneration.py              # E 层精确算例（秒级，默认）
python verify-degeneration.py --mc         # 蒙特卡洛大样本证伪（自落盘）
python verify-degeneration.py --data FILE  # 真实矩阵 JSON 数据入口
python verify-degeneration.py --print-template  # 输出契约模板
python -m pytest test_verify_degeneration.py -q # 21 例单元测试
```

产出文件：`verify-degeneration-real-results.txt`（E 层与 DATA 层）、`verify-degeneration-mc-results.txt`（MC 层）。表中全部数值转录自上述日志（2026-09-04，种子 $20240904$）。

完整核验器源码见 [framework.tex](framework.tex) 附录 A（逐字节嵌入，可独立复制运行）。
