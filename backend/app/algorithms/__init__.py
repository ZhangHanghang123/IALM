"""
IALM 5 号规则核心算法引擎
============================

实现银保监会 5 号规则三项监管核心指标：
- ALG-001 期限结构匹配率（≥ 80%）
- ALG-002 综合成本收益比（寿险 ≥ 1.05 / 财险 ≥ 1.10）
- ALG-003 现金流回正期（≤ 5 年）
- ALG-004 久期缺口（[-1, +1] 年）

算法设计参考：IALM_保险资产负债管理算法详细设计.md
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime
import numpy as np


# ═══════════════════════════════════════════════════════════════════════
# ALG-001: 期限结构匹配率（Duration Mismatch Ratio, DMR）
# ═══════════════════════════════════════════════════════════════════════
def calc_duration_match_ratio(
    asset_cashflows: List[Dict[str, Any]],
    liability_cashflows: List[Dict[str, Any]],
    bucket_years: int = 5,
) -> Dict[str, Any]:
    """
    ALG-001: 期限结构匹配率

    算法：
      1. 将资产/负债现金流按时间桶分组（默认 5 年一桶）
      2. 计算每个桶内资产占比 a_i 与负债占比 l_i
      3. 匹配率 = 1 - 0.5 * Σ|a_i - l_i|（Cowell & Smith 1992）
      4. 监管要求 ≥ 0.80

    Parameters:
      asset_cashflows: [{period_year: 1, amount: 1000}, ...] 资产端未来现金流
      liability_cashflows: [{period_year: 1, amount: 1200}, ...] 负债端未来现金流
      bucket_years: 时间桶宽度（默认 5 年）

    Returns:
      {
        "match_ratio": 0.85,            # 匹配率
        "status": "PASS",                # PASS/WARN/FAIL
        "asset_total": 50000,
        "liability_total": 55000,
        "asset_distribution": [...],     # 各桶资产占比
        "liability_distribution": [...], # 各桶负债占比
        "threshold": 0.80,
        "formula": "...",
      }
    """
    if not asset_cashflows or not liability_cashflows:
        return {
            "match_ratio": 0.0,
            "status": "FAIL",
            "error": "资产或负债现金流为空",
            "threshold": 0.80,
        }

    # 1. 求最大期数
    max_year = max(
        max((c["period_year"] for c in asset_cashflows), default=0),
        max((c["period_year"] for c in liability_cashflows), default=0),
    )
    num_buckets = (max_year + bucket_years - 1) // bucket_years

    # 2. 资产/负债按桶聚合
    asset_buckets = np.zeros(num_buckets)
    liability_buckets = np.zeros(num_buckets)
    for c in asset_cashflows:
        bucket_idx = min(int((c["period_year"] - 1) // bucket_years), num_buckets - 1)
        asset_buckets[bucket_idx] += float(c.get("amount", 0))
    for c in liability_cashflows:
        bucket_idx = min(int((c["period_year"] - 1) // bucket_years), num_buckets - 1)
        liability_buckets[bucket_idx] += float(c.get("amount", 0))

    asset_total = float(asset_buckets.sum())
    liability_total = float(liability_buckets.sum())

    if asset_total == 0 or liability_total == 0:
        return {"match_ratio": 0.0, "status": "FAIL", "error": "总现金流为 0"}

    # 3. 占比分布
    asset_dist = asset_buckets / asset_total
    liability_dist = liability_buckets / liability_total

    # 4. 匹配率（Cowell-Smith 公式）
    match_ratio = 1.0 - 0.5 * float(np.abs(asset_dist - liability_dist).sum())

    # 5. 状态判定
    if match_ratio >= 0.80:
        status = "PASS"
    elif match_ratio >= 0.70:
        status = "WARN"
    else:
        status = "FAIL"

    return {
        "match_ratio": round(match_ratio, 4),
        "status": status,
        "asset_total": round(asset_total, 2),
        "liability_total": round(liability_total, 2),
        "bucket_years": bucket_years,
        "num_buckets": int(num_buckets),
        "asset_distribution": [round(float(x), 4) for x in asset_dist],
        "liability_distribution": [round(float(x), 4) for x in liability_dist],
        "threshold": 0.80,
        "formula": "DMR = 1 - 0.5 * Σ|A_i/L_A - L_i/L_L|",
    }


# ═══════════════════════════════════════════════════════════════════════
# ALG-002: 综合成本收益比（Cost Yield Ratio, CYR）
# ═══════════════════════════════════════════════════════════════════════
def calc_cost_yield_ratio(
    investment_yield_rate: float,
    liability_cost_rate: float,
    expense_ratio: float = 0.03,
    company_type: str = "LIFE",
    tax_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    ALG-002: 综合成本收益比

    算法：
      CYR = 投资收益率(扣税后) / (负债资金成本 + 费用率)
      - 寿险阈值：≥ 1.05
      - 财险阈值：≥ 1.10

    Parameters:
      investment_yield_rate: 投资收益率（小数，0.045 表示 4.5%）
      liability_cost_rate: 负债资金成本（小数）
      expense_ratio: 费用率（默认 3%）
      company_type: LIFE/PROPERTY/REINSURANCE/HEALTH
      tax_rate: 所得税率

    Returns:
      {
        "ratio": 1.08,
        "status": "PASS",
        "net_yield": 0.045,
        "total_cost": 0.075,
        "threshold": 1.05,
      }
    """
    if company_type == "LIFE":
        threshold = 1.05
    elif company_type in ("PROPERTY", "HEALTH"):
        threshold = 1.10
    elif company_type == "REINSURANCE":
        threshold = 1.07
    else:
        threshold = 1.05

    net_yield = investment_yield_rate * (1 - tax_rate)
    total_cost = liability_cost_rate + expense_ratio
    ratio = net_yield / total_cost if total_cost > 0 else 0.0

    if ratio >= threshold:
        status = "PASS"
    elif ratio >= threshold - 0.05:
        status = "WARN"
    else:
        status = "FAIL"

    return {
        "ratio": round(ratio, 4),
        "status": status,
        "net_yield": round(net_yield, 6),
        "total_cost": round(total_cost, 6),
        "investment_yield_rate": investment_yield_rate,
        "liability_cost_rate": liability_cost_rate,
        "expense_ratio": expense_ratio,
        "tax_rate": tax_rate,
        "company_type": company_type,
        "threshold": threshold,
        "formula": "CYR = 投资收益率×(1-税率) / (负债成本 + 费用率)",
    }


# ═══════════════════════════════════════════════════════════════════════
# ALG-003: 现金流回正期（Cashflow Payback Period, CPP）
# ═══════════════════════════════════════════════════════════════════════
def calc_cashflow_payback_years(
    cumulative_net_cashflow: List[Dict[str, Any]],
    threshold: float = 5.0,
) -> Dict[str, Any]:
    """
    ALG-003: 现金流回正期

    算法：
      从起始点累加净现金流（资产收入 - 负债支出），找到首次 ≥ 0 的年份。
      若 < threshold 年，则满足监管要求。

    Parameters:
      cumulative_net_cashflow: [{year: 2025, net: -1000}, ...] 按年累计净现金流
      threshold: 监管阈值（默认 5 年）

    Returns:
      {
        "payback_years": 3.5,
        "status": "PASS",
        "break_even_year": 2028,
        "total_horizon": 10,
        "cumulative_curve": [...],
        "threshold": 5.0,
      }
    """
    if not cumulative_net_cashflow:
        return {"payback_years": None, "status": "FAIL", "error": "现金流数据为空"}

    # 找到首次累计 ≥ 0 的年份
    cum = 0.0
    payback_year = None
    prev_cum = 0.0
    prev_year = None
    for entry in cumulative_net_cashflow:
        cum += float(entry.get("net", 0))
        year = entry.get("year", 0)
        if cum >= 0 and payback_year is None:
            # 线性插值
            if prev_year is not None and prev_cum < 0:
                # 在 [prev_year, year] 区间内回正
                ratio = -prev_cum / (cum - prev_cum) if cum != prev_cum else 1.0
                payback_year = prev_year + ratio * (year - prev_year)
            else:
                payback_year = float(year)
            break
        prev_cum = cum
        prev_year = year

    # 转换为"距起始年的年数"（threshold 单位为"年"）
    start_year = cumulative_net_cashflow[0].get("year", 2025)
    if payback_year is not None:
        years_to_payback = payback_year - start_year
    else:
        years_to_payback = None

    if years_to_payback is None:
        status = "FAIL"
    elif years_to_payback <= threshold:
        status = "PASS"
    elif years_to_payback <= threshold + 2:
        status = "WARN"
    else:
        status = "FAIL"

    return {
        "payback_years": round(years_to_payback, 2) if years_to_payback is not None else None,
        "break_even_year": int(round(payback_year)) if payback_year is not None else None,
        "status": status,
        "total_horizon": len(cumulative_net_cashflow),
        "threshold": threshold,
        "formula": "回正期 = 使累计净现金流首次 ≥ 0 的年份（线性插值）",
    }


# ═══════════════════════════════════════════════════════════════════════
# ALG-004: 久期缺口（Duration Gap）
# ═══════════════════════════════════════════════════════════════════════
def calc_duration_gap(
    asset_cashflows: List[Dict[str, Any]],
    liability_cashflows: List[Dict[str, Any]],
    discount_rate: float = 0.03,
    min_gap: float = -1.0,
    max_gap: float = 1.0,
) -> Dict[str, Any]:
    """
    ALG-004: 久期与久期缺口

    算法：
      Macaulay Duration D = Σ(t·PV(CF_t)) / Σ(PV(CF_t))
      D_gap = D_asset - D_liability（资产 - 负债）
      阈值：[-1, +1] 年

    Returns:
      {
        "asset_duration": 7.5,
        "liability_duration": 8.2,
        "duration_gap": -0.7,
        "convexity_asset": 65.3,
        "convexity_liability": 72.8,
        "status": "PASS",
      }
    """
    def macaulay_duration(cashflows, y):
        pv_total = 0.0
        weighted = 0.0
        for cf in cashflows:
            t = float(cf.get("period_year", 0))
            amt = float(cf.get("amount", 0))
            pv = amt / ((1 + y) ** t) if y > 0 else amt
            pv_total += pv
            weighted += t * pv
        if pv_total == 0:
            return 0.0
        return weighted / pv_total

    def convexity(cashflows, y):
        pv_total = 0.0
        weighted = 0.0
        for cf in cashflows:
            t = float(cf.get("period_year", 0))
            amt = float(cf.get("amount", 0))
            if y > 0:
                pv = amt / ((1 + y) ** t)
                weighted += t * (t + 1) * pv
                pv_total += pv
        if y > 0 and pv_total > 0:
            return weighted / (pv_total * (1 + y) ** 2)
        return 0.0

    D_a = macaulay_duration(asset_cashflows, discount_rate)
    D_l = macaulay_duration(liability_cashflows, discount_rate)
    gap = D_a - D_l
    C_a = convexity(asset_cashflows, discount_rate)
    C_l = convexity(liability_cashflows, discount_rate)

    if min_gap <= gap <= max_gap:
        status = "PASS"
    elif min_gap - 1 <= gap <= max_gap + 1:
        status = "WARN"
    else:
        status = "FAIL"

    return {
        "asset_duration": round(D_a, 4),
        "liability_duration": round(D_l, 4),
        "duration_gap": round(gap, 4),
        "convexity_asset": round(C_a, 4),
        "convexity_liability": round(C_l, 4),
        "discount_rate": discount_rate,
        "status": status,
        "threshold_min": min_gap,
        "threshold_max": max_gap,
        "formula": "D = Σ(t·PV(CF_t))/Σ(PV(CF_t)); Gap = D_A - D_L",
    }


# ═══════════════════════════════════════════════════════════════════════
# 综合接口：5 号规则三项核心 + 久期缺口一并输出
# ═══════════════════════════════════════════════════════════════════════
def rule_5_full_analysis(
    asset_cashflows: List[Dict[str, Any]],
    liability_cashflows: List[Dict[str, Any]],
    investment_yield_rate: float,
    liability_cost_rate: float,
    expense_ratio: float = 0.03,
    company_type: str = "LIFE",
    discount_rate: float = 0.03,
) -> Dict[str, Any]:
    """5 号规则完整分析：三项核心 + 久期缺口"""
    cum_net = []
    cum = 0.0
    base_year = 2025
    max_year = max(
        max((c["period_year"] for c in asset_cashflows), default=0),
        max((c["period_year"] for c in liability_cashflows), default=0),
    )
    asset_map = {c["period_year"]: c.get("amount", 0) for c in asset_cashflows}
    liability_map = {c["period_year"]: c.get("amount", 0) for c in liability_cashflows}
    for y in range(1, max_year + 1):
        a = asset_map.get(y, 0)
        l = liability_map.get(y, 0)
        cum += a - l
        cum_net.append({"year": base_year + y - 1, "net": round(cum, 2)})

    alg001 = calc_duration_match_ratio(asset_cashflows, liability_cashflows)
    alg002 = calc_cost_yield_ratio(
        investment_yield_rate=investment_yield_rate,
        liability_cost_rate=liability_cost_rate,
        expense_ratio=expense_ratio,
        company_type=company_type,
    )
    alg003 = calc_cashflow_payback_years(cum_net)
    alg004 = calc_duration_gap(asset_cashflows, liability_cashflows, discount_rate)

    statuses = [alg001["status"], alg002["status"], alg003["status"], alg004["status"]]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "WARN" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    return {
        "alg_001_duration_match": alg001,
        "alg_002_cost_yield": alg002,
        "alg_003_cashflow_payback": alg003,
        "alg_004_duration_gap": alg004,
        "overall_status": overall,
        "analysis_date": datetime.utcnow().isoformat(),
        "company_type": company_type,
    }