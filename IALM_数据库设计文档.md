# IALM 数据库设计文档

> 设计版本：V1.0  
> 设计日期：2026-08-25  
> 数据库：`ialm_db`（与 ALMD/IALMD/ALMT/CURV 共用 `almd` 用户）  
> 脚本：`backend/sql/init.sql`

---

## 一、设计原则

| 原则 | 说明 |
|---|---|
| **前缀约定** | 系统表 `sys_` 前缀，业务表 `ialm_` 前缀（与 ALMD/IALMD 一致） |
| **公共字段** | `id / status / is_deleted / created_by / updated_by / created_at / updated_at` |
| **状态码值** | `TINYINT status` (0=停用, 1=启用) / `VARCHAR exec_status` (PENDING/RUNNING/COMPLETED/FAILED) |
| **JSON 字段** | `<name>_json` 后缀，存扩展字段/快照 |
| **时间戳** | `created_at` 自动当前时间 / `updated_at` 自动 ON UPDATE |
| **逻辑删除** | `is_deleted` 字段而非物理删除 |
| **索引策略** | 主键 BIGINT AUTO_INCREMENT + 外键/查询字段 + 复合索引 (公司+日期) |
| **字符集** | `utf8mb4 + utf8mb4_bin`（与 ALMD 一致，区分大小写） |

---

## 二、ER 图概览（14 个域 46 张表）

```
┌────────────────────────────────────────────────────────────────────┐
│  [域 1] 系统管理 sys_ (10 张)                                       │
│   sys_user / sys_role / sys_user_role / sys_permission              │
│   sys_role_permission / sys_dict_type / sys_dict_data               │
│   sys_llm_config / sys_audit_log / sys_notification                 │
└────────────────────────────────────────────────────────────────────┘
                                ↓ 用户属于
┌────────────────────────────────────────────────────────────────────┐
│  [域 2] 基础数据 (1 张)                                              │
│   ialm_insurance_company  ← 保险公司主档                              │
└────────────────────────────────────────────────────────────────────┘
       ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐
│[域3]资产端(6) │  │ [域4] 负债端 (8)   │  │ [域5] 市场数据(5) │
│ ialm_asset_  │  │ ialm_product_     │  │ ialm_yield_curve │
│ category     │  │ category          │  │ ialm_yield_curve │
│ ialm_asset_  │  │ ialm_policy_master│  │  _point          │
│ holding      │  │ ialm_reserve      │  │ ialm_fx_rate     │
│ ialm_asset_  │  │ ialm_actuarial_   │  │ ialm_equity_index│
│ cashflow     │  │ assumption        │  │ ialm_credit_spread│
│ ialm_asset_  │  │ ialm_mortality_   │  └                  │
│ risk_metric  │  │ table + point     │                      │
└──────────────┘  │ ialm_lapse_rate   │                      │
                  │ ialm_liability_   │                      │
                  │ cashflow          │                      │
                  └──────────────────┘                      │
       ↓                  ↓                  ↓              ↓
┌────────────────────────────────────────────────────────────────────┐
│  [域 6] 计算结果 (2 张)                                              │
│  ialm_match_analysis  ← 5号规则三项核心指标 (期限/成本收益/回正期)     │
│  ialm_cashflow_forecast                                               │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
       ↓                                              ↓
┌─────────────────────────────────┐  ┌────────────────────────────────┐
│ [域 7] 压力测试 (2 张)            │  │ [域 8] 投资组合 + 业绩归因 (2 张)│
│ ialm_stress_scenario             │  │ ialm_portfolio_allocation      │
│ ialm_stress_result               │  │ ialm_performance_attribution   │
└─────────────────────────────────┘  └────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  [域 9] 监管报表 (1 张)         ialm_regulatory_report                │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  [域 10] 风险预警 (3 张)                                            │
│  ialm_risk_preference / ialm_risk_indicator / ialm_risk_event        │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  [域 11] 模型管理 (3 张)                                            │
│  ialm_model_definition (14 种算法) / ialm_model_version             │
│  ialm_model_parameter                                               │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  [域 12] 工作流 (3 张)         ialm_workflow_def/_exec/_node_exec   │
│  [域 13] 智能对话 (2 张)       ialm_chat_session/_message             │
└────────────────────────────────────────────────────────────────────┘
```

---

## 三、表清单（46 张）

### 3.1 系统层 sys_ (10 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| sys_user | username/password_hash/company_id | IALM 用户（区别于 ALMD） |
| sys_role | role_code | 角色：ALCO_CHAIR/RISK_MANAGER/ACTUARY/ASSET_MANAGER/ADMIN |
| sys_user_role | user_id+role_id | 用户角色关联 |
| sys_permission | permission_code/type | 权限（菜单/按钮/API） |
| sys_role_permission | role_id+permission_id | 角色权限 |
| sys_dict_type | dict_type | 字典类型 |
| sys_dict_data | dict_type/value | 字典数据 |
| sys_llm_config | provider/model_name/api_key | LLM 配置 |
| sys_audit_log | user_id/action/entity | 审计日志 |
| sys_notification | user_id/level | 通知消息 |

### 3.2 基础 (1 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_insurance_company** | company_code/company_type/regulatory_rating | 保险公司主档（含寿险/财险/健康险/再保/集团） |

### 3.3 资产端 (6 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_asset_category** | category_code/parent_id/risk_weight | 资产分类树（现金/债券/权益/基金/另类/其他） |
| **ialm_asset_holding** | asset_code/duration_year/convexity/coupon_rate/maturity_date | 持仓明细 |
| **ialm_asset_cashflow** | holding_id/period_date/cashflow_type/present_value | 资产现金流（按期） |
| **ialm_asset_risk_metric** | metric_type (VAR/CVAR/CREDIT)/confidence_level | 风险指标 |
| ialm_asset_class_master | （备用） | 资产类别主数据 |
| ialm_holding_history | （合并到 asset_holding 历史分区） | 持仓变更历史 |

### 3.4 负债端 (8 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_product_category** | product_type_code/insurance_type/is_risk_account | 产品分类树（寿险/健康/年金/万能/投连） |
| **ialm_policy_master** | policy_no/sum_insured/payment_period/insurance_period/status | 保单主档（千万级） |
| **ialm_reserve** | reserve_type (UNEARNED/IBNR/CSM/EV)/accounting_basis | 准备金（CHINA_GAAP/IFRS17） |
| **ialm_actuarial_assumption** | assumption_set_code/discount_rate | 精算假设集 |
| **ialm_mortality_table** | table_code/gender | 死亡率表定义 |
| **ialm_mortality_table_point** | table_id/age/qx | 死亡率表点 |
| ialm_lapse_rate | rate_code/rate_value | 退保率假设 |
| **ialm_liability_cashflow** | period_date/cashflow_type (PREMIUM/CLAIM/SURRENDER)/scenario_code | 负债现金流（按期） |

### 3.5 市场数据 (5 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_yield_curve** | curve_code (GOVT_BOND/POLICY/CREDIT/SHIBOR)/curve_type | 收益率曲线定义 |
| **ialm_yield_curve_point** | curve_id/tenor/rate | 曲线点（0.083~30 年） |
| **ialm_fx_rate** | currency_pair/bid/ask/mid | 汇率 |
| **ialm_equity_index** | index_code/close_price/change_rate | 股票指数 |
| **ialm_credit_spread** | rating/tenor/spread_bps | 信用利差 |

### 3.6 计算结果 (2 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_match_analysis** | duration_match_ratio/cost_yield_ratio/cashflow_payback_years | **5号规则三项核心指标** + detail_json |
| **ialm_cashflow_forecast** | total_pv_asset/total_pv_liability/irr/scenario_code | 现金流预测结果 |

### 3.7 压力测试 (2 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_stress_scenario** | scenario_code/scenario_type/source/shocks_json | 情景定义（监管/自定义/历史） |
| **ialm_stress_result** | asset_impact/nav_change/solvency_ratio_after/liquidity_gap/n_paths | 压力测试结果（Monte Carlo 路径数） |

### 3.8 投资组合 (2 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_portfolio_allocation** | optimization_method (MEAN_VARIANCE/BLACK_LITTERMAN/RISK_PARITY)/weight/sharpe | 资产配置方案 |
| **ialm_performance_attribution** | allocation_effect/selection_effect/interaction_effect | Brinson 归因 |

### 3.9 监管报表 (1 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_regulatory_report** | report_type (QUANT_EVAL/CAPABILITY/STRESS/MATCH/MONTHLY)/report_period/file_path | 监管报表生成与报送 |

### 3.10 风险预警 (3 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_risk_preference** | duration_gap_min_max/match_min/payback_max/cost_yield_min | 风险偏好阈值 |
| **ialm_risk_indicator** | indicator_code/current_value/threshold_green_yellow_red/alert_level | KRI 实时监控 |
| **ialm_risk_event** | event_level/status (OPEN/INVESTIGATING/RESOLVED)/trigger_value | 风险事件 |

### 3.11 模型管理 (3 张)

| 表名 | 关键字段 | 说明 |
|---|---|---|
| **ialm_model_definition** | model_code (ALG-001..ALG-014)/category/priority/regulatory_code | 14 种算法模型定义 |
| **ialm_model_version** | version_code/parameters_json/benchmark_metrics_json | 模型版本 |
| **ialm_model_parameter** | param_code/param_value/default_value | 模型参数 |

### 3.12 工作流 (3 张) — 沿用 ALMD 多 Agent 引擎

| 表名 | 说明 |
|---|---|
| ialm_workflow_def | 工作流定义 (DAG JSON) |
| ialm_workflow_exec | 执行记录 |
| ialm_workflow_node_exec | 节点执行记录 |

### 3.13 智能对话 (2 张) — 沿用 ALMD chat

| 表名 | 说明 |
|---|---|
| ialm_chat_session | 对话 session |
| ialm_chat_message | 对话消息（user/assistant） |

---

## 四、与 ALMD/IALMD 的关键设计差异

| 维度 | ALMD/IALMD | IALM |
|---|---|---|
| 机构类型 | 银行/保险公司 | **保险公司** (LIFE/PROPERTY/HEALTH/REINSURANCE/GROUP) |
| 核心实体 | 银行机构 + 报告 | **保险公司 + 资产持仓 + 保单主档 + 产品分类** |
| 指标表 | 指标定义 + 指标值 | **期限匹配率/成本收益比/回正期/久期缺口** (5号规则三项) |
| 时间频率 | T+1 季度/年度 | **多频率（日/月/季/年）** - 现金流预测时间步长可配 |
| 计算字段 | 简单数值 | **含 JSON 详情 (detail_json/shocks_json)** 用于多因子分解 |
| 情景管理 | 无 | **独立的 stress_scenario + stress_result 两表**（Monte Carlo 路径数） |
| 寿命周期 | 报告类型枚举固定 | **保单 status: IN_FORCE/LAPSED/MATURED/SURRENDERED** |
| 准备金 | 无 | **reserve 表（含 CHINA_GAAP/IFRS17 双套会计准则）** |
| 精算假设 | 无 | **actuarial_assumption + mortality_table + lapse_rate 完整体系** |

---

## 五、核心 KPI 计算字段映射（5号规则）

| 算法 | 表 | 关键计算字段 | 监管阈值 |
|---|---|---|---|
| **ALG-001 期限结构匹配率** | ialm_match_analysis.duration_match_ratio | Σ min(D^A_i, D^L_i) / Σ D^L_i | ≥ 0.80 |
| **ALG-002 综合成本收益比** | ialm_match_analysis.cost_yield_ratio | ΣA·r / ΣL·(i+m+e) | 寿险 ≥1.05 / 财险 ≥1.10 |
| **ALG-003 现金流回正期** | ialm_match_analysis.cashflow_payback_years | min{t : NC_t≥0 ∀s≤t} | 风险账户 ≤ 5 |
| ALG-005 久期缺口 | ialm_match_analysis.duration_gap_years | D_A - D_L | [-1, +1] 容忍 |
| ALG-008 压力测试 NAV | ialm_stress_result.nav_change | -(DGAP)·Δy·A + 0.5·(C_A·A - C_L·L)·(Δy)² | 净资产不突破阈值 |

---

## 六、初始数据

- 5 个角色（ALCO_CHAIR/RISK_MANAGER/ACTUARY/ASSET_MANAGER/ADMIN）
- 17 个权限（菜单+按钮）
- **14 项算法模型**定义（对应算法详细设计 §1.3）
- **6 个监管预置压力情景**（利率+200/-200bp/退保+50%/投资-50%/汇率+15%/综合）

---

## 七、部署检查清单

| 检查项 | 状态 |
|---|---|
| 数据库 `ialm_db` 已创建 | ⏳ 待执行 |
| MySQL 用户 `almd` 有访问权限 | ⏳ 待执行 |
| 字符集 `utf8mb4` | ✅ 设计中已声明 |
| 46 张表 DDL 全部可执行 | ✅ 语法已验证 |
| 索引覆盖（公司+日期） | ✅ 已建复合索引 |
| JSON 字段用 MySQL 5.7+ 原生 JSON | ✅ |
| 与 ALMD/IALMD/ALMT/CURV 共用账号 `almd` | ✅ 设计一致 |

---

> **下一步**：
> 1. 在服务器 MySQL 创建 `ialm_db` 数据库
> 2. 导入 `backend/sql/init.sql` 初始化表结构 + 初始数据
> 3. 设计 FastAPI 后端模块 + SQLAlchemy ORM 模型
> 4. 设计 React + AntD 前端页面（与 ALMD/IALMD 一致风格）
> 5. 实现 14 项算法引擎（NumPy + Pandas + cvxpy + scipy）
> 6. 部署到 `/ialm/` 路径（端口 8003，沿用统一门户）