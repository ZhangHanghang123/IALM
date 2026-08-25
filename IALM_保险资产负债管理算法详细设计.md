# 保险资产负债管理（IALM）算法详细设计

> 文档版本：V1.0  
> 编写日期：2026年8月25日  
> 文档状态：待评审  
> 关联文档：IALM_保险资产负债管理产品需求文档  
> 主责部门：中电金信产品管理部

---

## 一、文档说明

### 1.1 目的

本文档基于《IALM_保险资产负债管理产品需求文档》中识别的核心业务功能，对其中涉及的核心量化算法进行数学定义、计算步骤、输入输出、边界处理、性能优化与代码示例的详细说明，作为算法工程师、后端开发工程师、测试工程师的共同实现依据。

### 1.2 适用范围

适用于 IALM 平台全部量化计算模块，包括但不限于：
- 5号规则三项核心量化指标
- 现金流预测模型
- 压力测试引擎
- 投资组合优化模型
- 业绩归因模型

### 1.3 算法清单

| 编号 | 算法名称 | 所属模块 | 优先级 | 监管对应 |
|------|---------|---------|--------|---------|
| ALG-001 | 期限结构匹配率 | 匹配分析 | P0 | 5号规则 |
| ALG-002 | 综合成本收益比 | 匹配分析 | P0 | 5号规则 |
| ALG-003 | 现金流回正期 | 匹配分析 / 现金流预测 | P0 | 5号规则 |
| ALG-004 | 修正久期 / 有效久期 | 久期引擎 | P0 | - |
| ALG-005 | 久期缺口 | 久期引擎 | P0 | - |
| ALG-006 | 现金流贴现预测 | 现金流预测 | P0 | - |
| ALG-007 | 蒙特卡洛随机情景生成 | 压力测试 | P0 | 6号规则 |
| ALG-008 | 多因子冲击传导 | 压力测试 | P0 | 6号规则 |
| ALG-009 | 反向压力测试 | 压力测试 | P1 | 内部管理 |
| ALG-010 | 均值-方差资产配置 | 投资决策 | P1 | - |
| ALG-011 | Black-Litterman 配置 | 投资决策 | P1 | - |
| ALG-012 | Brinson 业绩归因 | 投资决策 | P2 | - |
| ALG-013 | VaR / CVaR 风险度量 | 风险监控 | P1 | - |
| ALG-014 | 再保险现金流影响测算 | 产品定价联动 | P2 | - |

### 1.4 通用约定

| 项目 | 约定 |
|------|------|
| 时间单位 | 内部计算统一使用"年"为基准 |
| 利率口径 | 名义年化利率，连续复利或离散复利需注明 |
| 现金流方向 | 流入为正，流出为负 |
| 货币单位 | 默认 CNY，多币种场景需指定币种 |
| 精度 | 中间计算保留 12 位有效数字，最终结果保留 4 位小数 |
| 数据频率 | 业务数据 T+1，市场数据日终 |
| 缺失值处理 | 缺数据记录标记并跳过，不参与计算 |

---

## 二、5号规则三项核心量化指标算法

### 2.1 ALG-001 期限结构匹配率

#### 2.1.1 业务定义

期限结构匹配率衡量保险公司资产端现金流期限与负债端现金流期限的匹配程度，是资产负债匹配管理的核心指标。监管要求期限结构匹配率不低于 **80%**。

#### 2.1.2 数学公式

$$
M_{duration} = \frac{\sum_{i=1}^{N} \min\left(D^A_i, D^L_i\right)}{\sum_{i=1}^{N} D^L_i}
$$

其中：
- $M_{duration}$：期限结构匹配率
- $D^A_i$：第 i 期资产端现金流到期期限（年）
- $D^L_i$：第 i 期负债端现金流到期期限（年）
- $N$：现金流期数

**变体公式（加权版）**：
$$
M_{duration} = 1 - \frac{\sum_{i=1}^{N} w_i \cdot |D^A_i - D^L_i|}{\sum_{i=1}^{N} w_i \cdot D^L_i}
$$

其中 $w_i = CF^L_i / \sum CF^L_i$ 为负债端现金流权重。

#### 2.1.3 输入输出

**输入**：
| 参数 | 类型 | 说明 |
|------|------|------|
| asset_cashflows | DataFrame | 资产端现金流，字段：期数、现金流、到期年 |
| liability_cashflows | DataFrame | 负债端现金流，字段：期数、现金流、到期年 |
| method | str | 计算方法：`simple` 或 `weighted` |

**输出**：
| 字段 | 类型 | 说明 |
|------|------|------|
| match_ratio | float | 期限结构匹配率，0~1 |
| detail | DataFrame | 每期匹配明细 |
| warning | bool | 是否触发 80% 阈值预警 |

#### 2.1.4 计算步骤

1. **数据对齐**：将资产端和负债端现金流按期对齐，构建现金流瀑布图
2. **期限聚合**：按到期年份聚合现金流，得到聚合后的现金流分布
3. **加权计算**：采用加权公式计算匹配率（默认加权）
4. **阈值校验**：匹配率 < 80% 时触发预警
5. **结果分解**：按产品线、账户、币种等多维度分解

#### 2.1.5 边界处理

| 边界场景 | 处理策略 |
|---------|---------|
| 资产现金流为零 | 匹配率记 0，触发告警 |
| 负债现金流为零 | 跳过该期，不参与计算 |
| 期限为负值（已逾期） | 按 0 处理并标记异常 |
| 单一现金流 > 100 年 | 单独标记，长期险特殊处理 |
| 数据缺失率 > 30% | 整批数据标记为不可信 |

#### 2.1.6 代码示例（Python）

```python
import pandas as pd
import numpy as np

def duration_match_ratio(asset_cf: pd.DataFrame, liab_cf: pd.DataFrame,
                         method: str = 'weighted') -> dict:
    """
    计算期限结构匹配率
    
    Parameters
    ----------
    asset_cf : DataFrame, columns=['period', 'cashflow', 'duration_year']
    liab_cf : DataFrame, columns=['period', 'cashflow', 'duration_year']
    method : 'simple' | 'weighted'
    
    Returns
    -------
    dict with 'match_ratio', 'detail', 'warning'
    """
    # 1. 数据对齐
    merged = pd.merge(asset_cf, liab_cf, on='period', 
                      suffixes=('_asset', '_liab'), how='outer').fillna(0)
    
    # 2. 加权计算
    if method == 'weighted':
        total_liab_cf = merged['cashflow_liab'].sum()
        if total_liab_cf == 0:
            return {'match_ratio': 0.0, 'warning': True, 
                    'detail': merged, 'error': '负债现金流为零'}
        
        merged['weight'] = merged['cashflow_liab'] / total_liab_cf
        merged['contrib'] = merged['weight'] * (
            1 - np.abs(merged['duration_year_asset'] - merged['duration_year_liab']) 
            / merged['duration_year_liab'].replace(0, 1)
        )
        match_ratio = merged['contrib'].sum()
    
    elif method == 'simple':
        min_dur = np.minimum(merged['duration_year_asset'], 
                              merged['duration_year_liab']).sum()
        total_liab = merged['duration_year_liab'].sum()
        match_ratio = min_dur / total_liab if total_liab > 0 else 0
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return {
        'match_ratio': round(match_ratio, 4),
        'detail': merged,
        'warning': match_ratio < 0.80,
        'threshold': 0.80
    }
```

---

### 2.2 ALG-002 综合成本收益比

#### 2.2.1 业务定义

综合成本收益比衡量保险公司投资收益对负债端成本的覆盖能力，反映公司的盈利能力与持续经营能力。

#### 2.2.2 数学公式

$$
R_{CR} = \frac{I_{yield}}{\sum_{i} (C_i + R_i + E_i)}
$$

其中：
- $R_{CR}$：综合成本收益比
- $I_{yield}$：综合投资收益率（年化）
- $C_i$：第 i 类负债的资金成本（预定利率 / 定价利率）
- $R_i$：第 i 类负债的风险边际
- $E_i$：第 i 类负债的费用率

**展开形式（按险种拆分）**：
$$
R_{CR} = \frac{\sum_{j} A_j \cdot r_j}{\sum_{j} L_j \cdot (i_j + m_j + e_j)}
$$

其中：
- $A_j, r_j$：第 j 类资产的规模和投资收益率
- $L_j, i_j, m_j, e_j$：第 j 类负债的规模、定价利率、风险边际、费用率

#### 2.2.3 阈值规则（参考）

| 公司类型 | 健康区间 | 警戒区间 | 危险区间 |
|---------|---------|---------|---------|
| 寿险公司 | ≥ 1.05 | 0.95 ~ 1.05 | < 0.95 |
| 财险公司 | ≥ 1.10 | 1.00 ~ 1.10 | < 1.00 |
| 健康险公司 | ≥ 1.05 | 0.95 ~ 1.05 | < 0.95 |

> 注：实际阈值由各家公司在风险偏好中自行设定，监管仅提供参考。

#### 2.2.4 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| asset_returns | DataFrame | 资产端收益数据：资产类别、规模、收益率 |
| liability_costs | DataFrame | 负债端成本数据：险种、规模、预定利率、风险边际、费用率 |

| 输出 | 类型 | 说明 |
|------|------|------|
| cost_yield_ratio | float | 综合成本收益比 |
| spread_yield | float | 利差益/损 |
| breakdown | DataFrame | 分险种明细 |

#### 2.2.5 计算步骤

1. 数据准备：按险种 × 资产类别 × 期限 三维聚合
2. 资产端综合收益率计算（规模加权）
3. 负债端综合成本率计算（规模加权）
4. 比值计算与分解
5. 利差益/损分析
6. 阈值校验与告警

---

### 2.3 ALG-003 现金流回正期

#### 2.3.1 业务定义

现金流回正期指资产端累计现金流首次覆盖负债端累计现金流的时间点。监管要求风险账户（短期险、万能险等）现金流回正期 ≤ **5年**。

#### 2.3.2 数学公式

设：
- $A_t$：第 t 期资产端现金流（流入为正）
- $L_t$：第 t 期负债端现金流（流出为正）

累计净现金流：
$$
NC_t = \sum_{s=0}^{t} (A_s - L_s)
$$

现金流回正期 $T^*$ 为：
$$
T^* = \min\{t : NC_t \geq 0, \forall s \leq t\}
$$

即首次累计净现金流转正的时间，且在此之前未出现"先负后正再负"的反复。

#### 2.3.3 输入输出

**输入**：
| 参数 | 类型 | 说明 |
|------|------|------|
| asset_cashflows | array | 资产端按期现金流 |
| liab_cashflows | array | 负债端按期现金流 |
| freq | str | 现金流频率：`daily`/`monthly`/`quarterly`/`yearly` |
| lookback_years | int | 最长观测年限 |

**输出**：
| 字段 | 类型 | 说明 |
|------|------|------|
| payback_period | float | 现金流回正期（年） |
| is_payback | bool | 是否在观测期内回正 |
| cum_net_cf | array | 累计净现金流序列 |

#### 2.3.4 计算步骤

1. 数据频率对齐（统一为月度或季度）
2. 累计净现金流计算
3. 首次非负点识别
4. 持续非负校验（避免"假回正"）
5. 回正期计算（如未回正，返回 -1）
6. 阈值校验（≤ 5 年）

#### 2.3.5 边界处理

| 边界场景 | 处理策略 |
|---------|---------|
| 观测期内未回正 | payback_period = -1, 触发高优先级告警 |
| 起始期累计为正 | payback_period = 0 |
| 数据缺失 | 采用相邻期插值填充，超过 3 期缺失标记异常 |
| 万能险结算波动 | 提取"稳态结算利率"作为测算基础 |

#### 2.3.6 代码示例

```python
def cashflow_payback_period(asset_cf: np.ndarray, liab_cf: np.ndarray,
                             freq: str = 'yearly') -> dict:
    """
    计算现金流回正期
    
    Returns
    -------
    dict: { 'payback_period': float, 'is_payback': bool, 
            'cum_net_cf': np.ndarray }
    """
    # 频率转换：年化系数
    freq_factor = {'daily': 365, 'monthly': 12, 
                   'quarterly': 4, 'yearly': 1}[freq]
    
    # 净现金流
    net_cf = asset_cf - liab_cf
    
    # 累计净现金流
    cum_net = np.cumsum(net_cf)
    
    # 寻找首次持续非负点
    n = len(cum_net)
    payback_period = -1
    
    for i in range(n):
        if cum_net[i] >= 0 and all(cum_net[j] >= 0 for j in range(i+1)):
            payback_period = i / freq_factor
            break
    
    return {
        'payback_period': payoff_period,
        'is_payback': payback_period > 0,
        'cum_net_cf': cum_net,
        'threshold_5y_passed': payback_period > 0 and payback_period <= 5
    }
```

---

## 三、久期与凸性计算

### 3.1 ALG-004 修正久期 / 有效久期

#### 3.1.1 修正久期（适用于普通债券）

$$
D_{mod} = \frac{D_{mac}}{1 + y/m}
$$

其中：
- $D_{mac}：麦考利久期
- $y$：到期收益率（年化）
- $m$：每年付息次数

麦考利久期：
$$
D_{mac} = \frac{\sum_{t=1}^{T} t \cdot \frac{CF_t}{(1+y/m)^t}}{\sum_{t=1}^{T} \frac{CF_t}{(1+y/m)^t}}
$$

#### 3.1.2 有效久期（适用于含权债券）

$$
D_{eff} = \frac{P(y - \Delta y) - P(y + \Delta y)}{2 \cdot P(y) \cdot \Delta y}
$$

其中 $\Delta y$ 通常取 0.0001（即 1bp）。

#### 3.1.3 凸性

$$
C = \frac{P(y - \Delta y) + P(y + \Delta y) - 2 \cdot P(y)}{P(y) \cdot (\Delta y)^2}
$$

#### 3.1.4 债券价格计算

```
P = sum over t: CF_t / (1 + y/m)^t  (零息或息票债券)
P = F / (1 + y)^T  (零息债券)
```

#### 3.1.5 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| cashflow_schedule | DataFrame | 现金流时间表：期数、现金流 |
| ytm | float | 到期收益率 |
| face_value | float | 面值 |
| coupon_rate | float | 票面利率 |
| payment_freq | int | 年付息次数 |
| is_option_adjusted | bool | 是否含权 |

| 输出 | 类型 | 说明 |
|------|------|------|
| macaulay_duration | float | 麦考利久期 |
| modified_duration | float | 修正久期 |
| effective_duration | float | 有效久期（含权时） |
| convexity | float | 凸性 |
| price | float | 债券理论价格 |

#### 3.1.6 性能优化

- 向量化计算：批量债券的久期计算用 NumPy 矩阵运算
- 缓存：相同现金流模式的债券缓存计算结果
- 并行化：资产池拆分后多进程并行计算

---

### 3.2 ALG-005 久期缺口

#### 3.2.1 数学公式

资产端加权修正久期：
$$
D_A = \frac{\sum_i A_i \cdot D^A_i}{\sum_i A_i}
$$

负债端加权修正久期：
$$
D_L = \frac{\sum_j L_j \cdot D^L_j}{\sum_j L_j}
$$

久期缺口：
$$
DGAP = D_A - D_L
$$

久期比率：
$$
DR = \frac{D_A}{D_L}
$$

#### 3.2.2 利率变动对净值的影响

$$
\Delta NAV \approx -DGAP \cdot \Delta y \cdot A
$$

其中 $\Delta NAV$ 为净值变化，$\Delta y$ 为利率变动（如 +100bp），$A$ 为资产规模。

#### 3.2.3 风险偏好应用

```
久期缺口监管建议：
- 容忍区间：[-1, +1]（年）
- 警戒区间：[-2, +1] 或 [1, 2]
- 危险区间：< -2 或 > 2
```

---

## 四、现金流预测模型

### 4.1 ALG-006 现金流贴现预测

#### 4.1.1 业务定义

基于精算假设，预测未来一段时间内资产端和负债端各期现金流，并计算净现金流、累计现金流等关键指标。

#### 4.1.2 负债端现金流预测

**模型分类**：

| 模型 | 适用险种 | 输入 |
|------|---------|------|
| 寿险现金流模型 | 寿险、年金险 | 死亡率、定价利率、缴费方式 |
| 非寿险链梯法 | 财险 | 赔款发展因子、IBNR |
| Bootstrap 法 | 短险、健康险 | 历史赔付数据 |
| 随机模型 | 投连、万能 | 投资收益率情景、退保假设 |

**寿险现金流示例公式**：

预期死亡给付（年度）：
$$
B_t^{death} = \sum_{policy} S_{policy} \cdot q_{x+t-1} \cdot (1 - q_{x+t-1})^{t-1} \cdot F_{policy}
$$

其中 $S_{policy}$ 为有效保单数，$q_x$ 为死亡率，$F$ 为保额。

预期退保：
$$
B_t^{surrender} = \sum_{policy} S_{policy}^{active} \cdot w_{x+t} \cdot CV_{policy}
$$

其中 $w_x$ 为退保率，$CV$ 为现金价值。

#### 4.1.3 资产端现金流预测

债券组合未来 t 期现金流：
$$
CF_t^A = \sum_{b} C_{b,t}^{coupon} + C_{b,t}^{principal} + C_{b,t}^{reinvest}
$$

再投资收益：
$$
RI_t = \sum_{s=0}^{t-1} CF_s^A \cdot r_s^{reinvest} \cdot \Delta t
$$

#### 4.1.4 净现金流与贴现

净现金流：
$$
NC_t = CF_t^A - CF_t^L
$$

净现金流贴现值：
$$
PV = \sum_{t=0}^{T} \frac{NC_t}{(1 + d)^t}
$$

其中 $d$ 为贴现率（与负债折现率一致）。

#### 4.1.5 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| policy_master | DataFrame | 保单主档数据 |
| assumption_set | dict | 精算假设（死亡率、退保率、利率等） |
| asset_master | DataFrame | 资产主档 |
| yield_curve | DataFrame | 收益率曲线 |
| forecast_horizon | int | 预测年限 |
| time_step | str | 时间步长（日/月/季/年） |

| 输出 | 类型 | 说明 |
|------|------|------|
| liability_cf | DataFrame | 负债端各期现金流 |
| asset_cf | DataFrame | 资产端各期现金流 |
| net_cf | DataFrame | 净现金流 |
| pv_metrics | dict | PV、IRR、久期等指标 |

#### 4.1.6 性能优化策略

1. **保单分组聚合**：按产品、年龄、性别、保额分组聚合，而非单笔计算
2. **精算表预计算**：预先计算生命表、退保率表到内存
3. **向量化运算**：利用 NumPy 矩阵运算代替 Python 循环
4. **并行计算**：不同产品线并行计算
5. **结果缓存**：相同假设下的结果缓存

---

## 五、压力测试算法

### 5.1 ALG-007 蒙特卡洛随机情景生成

#### 5.1.1 业务定义

基于历史数据和市场模型，生成未来利率、汇率、收益率等多因子的随机情景路径，用于压力测试。

#### 5.1.2 单因子模型：Vasicek / CIR

**Vasicek 模型**：
$$
dr_t = a(b - r_t) dt + \sigma dW_t
$$

其中：
- $r_t$：短期利率
- $a$：均值回归速度
- $b$：长期均值
- $\sigma$：波动率
- $dW_t$：维纳过程

**CIR 模型**（避免负利率）：
$$
dr_t = a(b - r_t) dt + \sigma \sqrt{r_t} dW_t
$$

#### 5.1.3 利率期限结构模型：Hull-White

$$
dr_t = (\theta_t - a r_t) dt + \sigma dW_t
$$

其中 $\theta_t$ 用于拟合初始期限结构：
$$
\theta_t = \frac{\partial f(0,t)}{\partial t} + a f(0,t) + \frac{\sigma^2}{2a}(1 - e^{-2at})
$$

其中 $f(0,t)$ 为初始瞬时远期利率。

#### 5.1.4 多因子模型

利率 + 汇率 + 股票的多因子模型：

$$
d\begin{pmatrix} r \\ FX \\ S \end{pmatrix} = 
\begin{pmatrix} \mu_r \\ \mu_{fx} \\ \mu_s \end{pmatrix} dt + 
\Sigma \begin{pmatrix} dW_1 \\ dW_2 \\ dW_3 \end{pmatrix}
$$

其中 $\Sigma$ 为协方差矩阵（含相关性）。

#### 5.1.5 离散化模拟（Euler-Maruyama）

```python
def hull_white_simulation(theta, a, sigma, r0, T, dt, n_paths):
    """
    Hull-White 模型蒙特卡洛模拟
    
    Parameters
    ----------
    theta : array, 利率漂移函数
    a : float, 均值回归速度
    sigma : float, 波动率
    r0 : float, 初始利率
    T : int, 模拟期限（年）
    dt : float, 时间步长（年）
    n_paths : int, 模拟路径数
    
    Returns
    -------
    paths : ndarray, shape (n_paths, int(T/dt)+1)
    """
    n_steps = int(T / dt)
    paths = np.zeros((n_paths, n_steps + 1))
    paths[:, 0] = r0
    
    sqrt_dt = np.sqrt(dt)
    for i in range(n_steps):
        t = i * dt
        drift = (theta[i] - a * paths[:, i]) * dt
        diffusion = sigma * sqrt_dt * np.random.standard_normal(n_paths)
        paths[:, i+1] = paths[:, i] + drift + diffusion
    
    return paths
```

#### 5.1.6 路径性能优化

| 数据规模 | 优化策略 |
|---------|---------|
| 路径数 < 1,000 | 单进程 |
| 1,000 ~ 10,000 | 多进程并行 |
| 10,000 ~ 100,000 | NumPy 向量化 + 多进程 |
| > 100,000 | GPU 加速（CuPy）或分布式 |

---

### 5.2 ALG-008 多因子冲击传导

#### 5.2.1 业务定义

将预设的冲击情景（如利率 +200bp、退保率 +50%）传导至资产端、负债端，计算各项指标变化。

#### 5.2.2 冲击情景定义

| 因子 | 监管情景 | 默认情景 |
|------|---------|---------|
| 利率 | 平行 +200bp / -200bp | 用户自定义 |
| 退保率 | +50% | 用户自定义 |
| 死亡率 | +10%（寿险） / -10% | 用户自定义 |
| 汇率 | USD/CNY ±15% | 用户自定义 |
| 投资收益率 | -50% | 用户自定义 |

#### 5.2.3 利率冲击传导

**资产端**：
$$
\Delta A = -D_A \cdot A \cdot \Delta y + \frac{1}{2} C_A \cdot A \cdot (\Delta y)^2
$$

**负债端**：
$$
\Delta L = -D_L \cdot L \cdot \Delta y + \frac{1}{2} C_L \cdot L \cdot (\Delta y)^2
$$

**净资产变化**：
$$
\Delta NAV = \Delta A - \Delta L = -(D_A A - D_L L) \Delta y + \frac{1}{2}(C_A A - C_L L) (\Delta y)^2
$$

#### 5.2.4 退保冲击传导

退保率假设变化导致负债现金流变化：

**现金流重估**：
$$
CF_t^{L,new} = CF_t^{L,base} \cdot (1 + \alpha \cdot \Delta w_t)
$$

其中 $\alpha$ 为传导系数，$\Delta w_t$ 为退保率冲击。

**流动性需求测算**：
```
流动性缺口 = sum(新增退保给付) - sum(可用流动性资产)
```

#### 5.2.5 综合压力测试

多因子同时冲击：
$$
\mathbf{\Delta} = \mathbf{S} \cdot \mathbf{\Delta X}
$$

其中 $\mathbf{S}$ 为敏感度矩阵，$\mathbf{\Delta X}$ 为冲击向量。

#### 5.2.6 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| scenario_set | dict | 冲击情景定义 |
| portfolio_state | dict | 当前资产负债状态 |
| pricing_assumption | dict | 精算假设 |

| 输出 | 类型 | 说明 |
|------|------|------|
| asset_impact | DataFrame | 资产端影响 |
| liability_impact | DataFrame | 负债端影响 |
| nav_change | float | 净资产变化 |
| solvency_ratio | float | 偿付能力充足率变化 |
| liquidity_gap | float | 流动性缺口 |

---

### 5.3 ALG-009 反向压力测试

#### 5.3.1 业务定义

从监管阈值出发，反向寻找会导致风险指标突破阈值的极端情景，识别公司"风险边界"。

#### 5.3.2 算法步骤

1. **定义目标函数**：$f(x) = $ 风险指标（如偿付能力充足率）
2. **设定约束条件**：$f(x) \leq T$（监管阈值）
3. **求解边界**：寻找使 $f(x) = T$ 的极端 $x^*$
4. **识别关键因子**：分解 $x^*$ 的因子贡献

#### 5.3.3 数学表述

$$
x^* = \arg\max_{x \in \Omega} \|x - x_0\|, \quad \text{s.t.} \quad f(x^*) = T
$$

其中 $x_0$ 为基准情景，$\Omega$ 为可行域。

#### 5.3.4 实现方法

| 方法 | 适用场景 | 优缺点 |
|------|---------|--------|
| 二分搜索 | 单因子冲击 | 简单稳定 |
| 梯度下降 | 多因子冲击 | 高效但需可微 |
| 序贯单因子 | 多因子组合 | 直观易解释 |
| 蒙特卡洛拒绝采样 | 非线性场景 | 准确但耗时 |
| 贝叶斯优化 | 高维场景 | 高效但复杂 |

---

## 六、投资组合优化

### 6.1 ALG-010 均值-方差资产配置（Markowitz）

#### 6.1.1 业务定义

基于 Markowitz 均值-方差模型，求解给定风险下的最优资产配置，或给定收益下的最小风险配置。

#### 6.1.2 数学模型

**最小方差模型**：
$$
\min_{w} \frac{1}{2} w^T \Sigma w
$$
$$
\text{s.t.} \quad w^T \mu \geq R_{target}, \quad \mathbf{1}^T w = 1, \quad w \geq 0
$$

**最大夏普比率模型**：
$$
\max_{w} \frac{w^T \mu - r_f}{\sqrt{w^T \Sigma w}}
$$
$$
\text{s.t.} \quad \mathbf{1}^T w = 1, \quad w \geq 0
$$

其中：
- $w$：资产权重向量
- $\mu$：预期收益率向量
- $\Sigma$：协方差矩阵
- $r_f$：无风险利率

#### 6.1.3 求解方法

| 方法 | 适用规模 | 库 |
|------|---------|-----|
| 二次规划（QP） | < 100 资产 | cvxpy, scipy |
| 临界线法 | < 50 资产 | PyPortfolioOpt |
| 内点法 | < 500 资产 | 内置 |
| 启发式算法 | > 1000 资产 | 自实现GA/PSO |

#### 6.1.4 代码示例

```python
import cvxpy as cp
import numpy as np

def mean_variance_optimize(mu: np.ndarray, sigma: np.ndarray, 
                            rf: float = 0.025) -> np.ndarray:
    """
    均值-方差最优化（最大夏普比率）
    
    Parameters
    ----------
    mu : 预期收益率向量 (n,)
    sigma : 协方差矩阵 (n, n)
    rf : 无风险利率
    
    Returns
    -------
    w : 最优权重 (n,)
    """
    n = len(mu)
    w = cp.Variable(n)
    
    # 目标：最大化夏普比率
    excess_return = mu - rf
    risk = cp.quad_form(w, cp.psd_wrap(sigma))
    
    objective = cp.Maximize(excess_return @ w - 0.5 * risk)
    constraints = [
        cp.sum(w) == 1,
        w >= 0,
        w <= 0.4,  # 单资产上限
    ]
    
    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.SCS)
    
    if prob.status != 'optimal':
        raise ValueError(f"Optimization failed: {prob.status}")
    
    return w.value
```

#### 6.1.5 约束条件扩展

支持业务约束：
- 单资产权重上限
- 资产类别权重区间
- 行业集中度限制
- 久期约束
- 监管比例限制（如权益类 ≤ 30%）

---

### 6.2 ALG-011 Black-Litterman 配置模型

#### 6.2.1 业务定义

在均值-方差基础上，融合投资者主观观点和市场均衡收益，得到更稳健的配置方案。

#### 6.2.2 核心步骤

**Step 1：市场隐含均衡收益（Reverse Optimization）**
$$
\Pi = \lambda \Sigma w_{mkt}
$$

其中 $w_{mkt}$ 为市值权重，$\lambda = (w_{mkt}^T \mu - r_f) / (w_{mkt}^T \Sigma w_{mkt})$。

**Step 2：观点设置**
- 观点矩阵 $P$（k×n，k 为观点数，n 为资产数）
- 观点收益向量 $Q$（k×1）
- 观点信心矩阵 $\Omega$（k×k）

**Step 3：后验收益**
$$
E[R] = [(\tau \Sigma)^{-1} + P^T \Omega^{-1} P]^{-1} [(\tau \Sigma)^{-1} \Pi + P^T \Omega^{-1} Q]
$$

**Step 4：配置权重**
$$
w^* = (\lambda \Sigma)^{-1} E[R]
$$

#### 6.2.3 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| market_caps | array | 各资产市值 |
| cov_matrix | array | 协方差矩阵 |
| views | list | 主观观点列表 |
| tau | float | 缩放因子（默认 0.05）|
| rf | float | 无风险利率 |

| 输出 | 类型 | 说明 |
|------|------|------|
| equilibrium_return | array | 均衡收益 |
| posterior_return | array | 后验收益 |
| optimal_weights | array | 最优权重 |
| view_contributions | DataFrame | 观点贡献分解 |

---

## 七、业绩归因

### 7.1 ALG-012 Brinson 业绩归因

#### 7.1.1 业务定义

将投资组合的超额收益分解为：资产配置贡献（Allocation）、证券选择贡献（Selection）、交互贡献（Interaction）。

#### 7.1.2 单期 Brinson 模型

$$
R_{p} - R_{b} = \sum_{i=1}^{N} (w_i^p - w_i^b) R_i^b + \sum_{i=1}^{N} w_i^b (R_i^p - R_i^b) + \sum_{i=1}^{N} (w_i^p - w_i^b)(R_i^p - R_i^b)
$$

简记：
$$
\text{超额收益} = \text{配置效应} + \text{选择效应} + \text{交互效应}
$$

其中：
- $w_i^p, w_i^b$：组合和基准在第 i 类资产的权重
- $R_i^p, R_i^b$：组合和基准在第 i 类资产的收益率

#### 7.1.3 多期归因（Modified Brinson）

**Cariño 平滑法**：
$$
\text{Link}_t = \text{Link}_{t-1} \cdot (1 + R_{p,t}) / (1 + R_{b,t})
$$

各效应累积时按归一化权重分配：
$$
\text{Allocation}_T = \sum_t \alpha_t \cdot \text{Link}_t \cdot \text{Allocation}_t^{单期}
$$

其中 $\alpha_t$ 为时点权重。

#### 7.1.4 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| portfolio_holdings | DataFrame | 组合持仓（多期） |
| benchmark_holdings | DataFrame | 基准持仓（多期） |
| asset_returns | DataFrame | 各资产收益率 |

| 输出 | 类型 | 说明 |
|------|------|------|
| total_excess | float | 总超额收益 |
| allocation_effect | float | 配置效应 |
| selection_effect | float | 选择效应 |
| interaction_effect | float | 交互效应 |
| breakdown | DataFrame | 按资产类别分解 |

---

## 八、风险度量

### 8.1 ALG-013 VaR / CVaR 风险度量

#### 8.1.1 历史模拟法 VaR

**算法步骤**：
1. 收集 N 期历史收益率序列
2. 按收益率升序排序
3. 取第 (1-α)N 个分位数即为 VaR

$$
VaR_{\alpha} = -q_{\alpha}(R)
$$

其中 $q_{\alpha}$ 为 α 分位数。

#### 8.1.2 参数法 VaR（正态分布假设）

$$
VaR_{\alpha} = -(\mu - z_{\alpha} \sigma) \cdot V
$$

其中 $z_{\alpha}$ 为标准正态分布 α 分位数，$V$ 为组合价值。

#### 8.1.3 CVaR（条件 VaR / Expected Shortfall）

$$
CVaR_{\alpha} = -\mathbb{E}[R | R \leq -VaR_{\alpha}]
$$

即超过 VaR 的损失的平均值。

#### 8.1.4 蒙特卡洛 VaR

```python
def monte_carlo_var(returns, n_sims=10000, alpha=0.05):
    """
    蒙特卡洛 VaR 计算
    """
    mu = returns.mean()
    sigma = returns.std()
    
    # 模拟未来收益率
    sim_returns = np.random.normal(mu, sigma, n_sims)
    
    # 排序找分位
    var = -np.percentile(sim_returns, alpha * 100)
    cvar = -sim_returns[sim_returns <= -var].mean()
    
    return {'VaR': var, 'CVaR': cvar}
```

#### 8.1.5 投资应用

- 持仓层面：单资产 VaR
- 组合层面：组合 VaR（考虑相关性）
- 账户层面：账户整体 VaR

---

## 九、再保险现金流影响测算（ALG-014）

### 9.1 业务定义

测算不同再保方案（分出比例、限额、费率）对资产负债现金流的影响。

### 9.2 公式

**分出后净现金流**：
$$
CF_t^{net} = CF_t^{gross} - CF_t^{ceded} + CF_t^{recover}
$$

**分出摊回现金流**：
$$
CF_t^{recover} = \sum_{claim} \text{Claim} \cdot \text{RecoverRate}_t \cdot P(\text{Claim} > \text{Deductible})
$$

### 9.3 输入输出

| 输入 | 类型 | 说明 |
|------|------|------|
| reinsurance_plan | dict | 再保方案参数 |
| claim_distribution | DataFrame | 赔款分布 |
| retention_limit | float | 自留额 |

| 输出 | 类型 | 说明 |
|------|------|------|
| net_cashflows | DataFrame | 分出后净现金流 |
| ceded_premium | float | 分出保费 |
| expected_recover | float | 预期摊回 |
| net_loss_ratio | float | 分出后赔付率 |

---

## 十、算法性能与稳定性

### 10.1 性能指标要求

| 算法 | 数据规模 | 性能要求 |
|------|---------|---------|
| 期限结构匹配率 | 10万期 | ≤ 5秒 |
| 现金流预测（月度） | 30年×10万保单 | ≤ 10分钟 |
| 蒙特卡洛情景（1万路径） | 30年×5因子 | ≤ 30分钟 |
| 均值-方差优化 | 50资产 | ≤ 10秒 |
| Brinson 归因（月度） | 30资产×24月 | ≤ 5秒 |
| 综合压力测试 | 全量资产+负债 | ≤ 30分钟 |

### 10.2 优化技术栈

| 优化维度 | 技术方案 |
|---------|---------|
| 向量化 | NumPy 矩阵运算 |
| 并行化 | 多进程（multiprocessing）/ Dask |
| GPU 加速 | CuPy / RAPIDS / PyTorch |
| 分布式 | Spark / Ray |
| JIT 编译 | Numba |
| 高性能数值 | Cython / C 扩展 |

### 10.3 精度控制

| 控制项 | 策略 |
|--------|------|
| 浮点精度 | 使用 np.float64 |
| 数值稳定性 | 协方差矩阵正则化（$\Sigma + \epsilon I$） |
| 单调性校验 | 现金流、久期单调性检查 |
| 边界保护 | 除零、负利率、负久期等异常保护 |

### 10.4 异常处理

| 异常类型 | 处理策略 |
|---------|---------|
| 算法不收敛 | 回退到简化算法 + 告警 |
| 数据缺失率 > 阈值 | 标记任务为不可信，不输出结果 |
| 计算超时 | 自动拆分并行，重试机制 |
| 数值溢出 | 异常点过滤 + 任务中断 |

---

## 十一、算法验证与回溯

### 11.1 单元测试要求

| 算法 | 测试用例数（最低） |
|------|------------------|
| 期限结构匹配率 | 30+ |
| 综合成本收益比 | 20+ |
| 现金流回正期 | 30+ |
| 久期 / 凸性 | 40+ |
| 现金流预测 | 50+ |
| 蒙特卡洛 | 30+ |
| Markowitz | 30+ |
| Black-Litterman | 20+ |
| Brinson 归因 | 25+ |
| VaR / CVaR | 30+ |

### 11.2 回归测试样本

建立"金标样本库"：
- 手工计算的标杆结果（5~10 套）
- 历史监管报送口径结果（10~20 期）
- 行业公开案例（10~20 例）

### 11.3 回溯测试（Backtesting）

| 测试类型 | 方法 |
|---------|------|
| VaR 回溯 | Kupiec 检验、Christoffersen 检验 |
| 现金流预测 | MAPE、RMSE 评估 |
| 压力测试 | 历史情景回放比对 |
| 配置优化 | 历史业绩归因比对 |

### 11.4 模型治理

| 治理项 | 频率 |
|--------|------|
| 模型清单登记 | 新增即登记 |
| 参数更新评审 | 季度 |
| 模型回溯验证 | 半年 |
| 模型升级评估 | 年度 |
| 模型退役评估 | 触发式 |

---

## 十二、算法交付物

### 12.1 代码资产

| 资产 | 说明 |
|------|------|
| `alm_algorithms/` | 算法包 |
| `alm_algorithms/duration.py` | 久期/凸性 |
| `alm_algorithms/cashflow.py` | 现金流预测 |
| `alm_algorithms/stress_test.py` | 压力测试 |
| `alm_algorithms/optimization.py` | 配置优化 |
| `alm_algorithms/attribution.py` | 业绩归因 |
| `tests/` | 单元测试 |
| `benchmarks/` | 性能基准测试 |
| `examples/` | 使用示例 |

### 12.2 文档资产

| 文档 | 说明 |
|------|------|
| 算法 README | 总览 |
| 算法接口文档 | 函数签名、参数、返回值 |
| 算法验证报告 | 单元测试覆盖率、回溯结果 |
| 算法变更日志 | 版本迭代记录 |

---

## 十三、附录

### 附录A：核心数学符号表

| 符号 | 含义 |
|------|------|
| $A_i$ | 资产 i 的规模 |
| $L_i$ | 负债 i 的规模 |
| $D$ | 久期 |
| $y$ | 收益率 |
| $CF_t$ | 第 t 期现金流 |
| $PV$ | 现值 |
| $w$ | 权重向量 |
| $\Sigma$ | 协方差矩阵 |
| $\mu$ | 预期收益率向量 |
| $\theta_t$ | 漂移函数 |
| $\sigma$ | 波动率 |
| $r_f$ | 无风险利率 |
| $\lambda$ | 风险厌恶系数 |
| $\alpha, \beta$ | 显著性水平、回归系数 |

### 附录B：关键参考书目与论文

| 序号 | 名称 | 作者 |
|------|------|------|
| 1 | Asset-Liability Management | Z. Bodie, A. Marcus, C. Perroni |
| 2 | Financial Theory and Corporate Policy | T. Copeland, J. Weston, K. Shastri |
| 3 | Options, Futures, and Other Derivatives | J. Hull |
| 4 | Active Portfolio Management | G. Grinold, R. Kahn |
| 5 | Black-Litterman Model 原始论文 | Black & Litterman (1992) |
| 6 | Brinson 归因原始论文 | Brinson & Fachler (1985) |
| 7 | 《保险公司资产负债管理》 | 中国银保监会培训教材 |
| 8 | IFRS 17 Insurance Contracts | IASB |
| 9 | IAIS Insurance Core Principles | IAIS |
| 10 | Solvency II 技术文档 | EIOPA |

### 附录C：常用 Python 库

| 库 | 用途 |
|----|------|
| NumPy | 数值计算 |
| Pandas | 数据处理 |
| SciPy | 科学计算（优化、积分）|
| statsmodels | 统计模型 |
| cvxpy | 凸优化 |
| PyPortfolioOpt | 投资组合优化 |
| QuantLib | 金融工程库 |
| Numba | JIT 编译 |
| Dask | 并行计算 |
| CuPy | GPU 计算 |
| Matplotlib / Plotly | 可视化 |

### 附录D：版本修订记录

| 版本 | 日期 | 修订人 | 修订内容 |
|------|------|--------|---------|
| V1.0 | 2026-08-25 | 张行行 | 初稿，覆盖14项核心算法的详细设计 |

---

> **文档结束**
