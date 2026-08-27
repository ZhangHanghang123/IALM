"""
IALM 现金流测算引擎
- AssetCashflowEngine：按持仓的支付日程（freq+unit）+ 收益率曲线生成现金流
- LiabilityCashflowEngine：按保单的 mortality/lapse/expense 经验率生成现金流
- CashflowGenerationService：编排 + 持久化 + 报告
"""
from __future__ import annotations
import math
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional, List, Dict, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

# 单位换算：年化
UNIT_TO_YEARS = {
    'DAY': 1.0 / 365,
    'WEEK': 7 / 365,
    'MONTH': 1 / 12,
    'QUARTER': 0.25,
    'HALF_YEAR': 0.5,
    'YEAR': 1.0,
}

# 资产分类 → 现金流类型映射
CATEGORY_CASHFLOW_TYPE = {
    'CASH': 'INTEREST',
    'CASH-DEPOSIT': 'INTEREST',
    'CASH-INTERBANK': 'INTEREST',
    'CASH-MMF': 'INTEREST',
    'BOND': 'COUPON',
    'BOND-GOVT': 'COUPON',
    'BOND-POLICY': 'COUPON',
    'BOND-CDB': 'COUPON',
    'BOND-EXIMBANK': 'COUPON',
    'BOND-COMMERCIAL': 'COUPON',
    'BOND-BANK-T2': 'COUPON',
    'BOND-BANK-ORDINARY': 'COUPON',
    'BOND-CORP': 'COUPON',
    'BOND-CORP-AAA': 'COUPON',
    'BOND-CORP-AA': 'COUPON',
    'BOND-CORP-CITY': 'COUPON',
    'BOND-CONVERT': 'COUPON',
    'BOND-GOVT-10Y': 'COUPON',
    'BOND-GOVT-20Y': 'COUPON',
    'BOND-GOVT-30Y': 'COUPON',
    'EQUITY': 'DIVIDEND',
    'EQUITY-ASTOCK': 'DIVIDEND',
    'EQUITY-HSTOCK': 'DIVIDEND',
    'EQUITY-PREFERRED': 'DIVIDEND',
    'FUND': 'DISTRIBUTION',
    'FUND-EQUITY': 'DISTRIBUTION',
    'FUND-BOND': 'DISTRIBUTION',
    'FUND-MIXED': 'DISTRIBUTION',
    'FUND-MONETARY': 'DISTRIBUTION',
    'FUND-ETF': 'DISTRIBUTION',
    'FUND-GOLD': 'DISTRIBUTION',
    'ALTERNATIVE': 'DISTRIBUTION',
    'ALTERNATIVE-INFRA': 'DISTRIBUTION',
    'ALTERNATIVE-TRUST': 'DISTRIBUTION',
    'ALTERNATIVE-REITS': 'DISTRIBUTION',
    'LT-EQUITY': 'DIVIDEND',
    'LT-EQUITY-ASSOC': 'DIVIDEND',
    'LT-EQUITY-SUBSID': 'DIVIDEND',
    'REAL-ESTATE': 'RENTAL',
    'REAL-ESTATE-OFFICE': 'RENTAL',
    'REAL-ESTATE-RETAIL': 'RENTAL',
    'OTHER-INV': 'INTEREST',
    'OTHER-INV-CD': 'INTEREST',
    'OTHER-INV-DERIV': 'SETTLE',
    'OTHER-INV-AMC': 'DISTRIBUTION',
}


@dataclass
class YieldCurve:
    """贴现曲线（NSS 插值用）"""
    curve_code: str
    points: List[Tuple[float, float]]  # (tenor_year, rate)

    def get_rate(self, t: float) -> float:
        """线性插值获取 t 年期收益率"""
        if not self.points:
            return 0.03
        t = max(0.0, t)
        pts = sorted(self.points, key=lambda x: x[0])
        if t <= pts[0][0]:
            return pts[0][1]
        if t >= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= t <= x1:
                # log-linear 插值
                w = (t - x0) / (x1 - x0)
                return y0 * (1 - w) + y1 * w
        return 0.03

    def discount_factor(self, t: float) -> float:
        r = self.get_rate(t)
        if t <= 0:
            return 1.0
        return 1.0 / (1.0 + r) ** t


@dataclass
class AssetCashflowRow:
    holding_id: int
    company_id: int
    asset_code: str
    period_number: int
    period_date: date
    period_year: float
    cashflow_type: str
    amount: float
    discount_factor: float
    present_value: float
    scenario_code: str = 'BASE'


@dataclass
class LiabilityCashflowRow:
    company_id: int
    product_type_id: int
    policy_id: int
    period_number: int
    period_date: date
    period_year: float
    cashflow_type: str  # PREMIUM_IN / CLAIM_OUT / BENEFIT_OUT / SURRENDER_OUT / EXPENSE_OUT
    amount: float
    discount_factor: float
    present_value: float
    scenario_code: str = 'BASE'


# ════════════════════════════════════════════════════════════
# 资产端引擎
# ════════════════════════════════════════════════════════════
class AssetCashflowEngine:
    """
    资产现金流引擎
    - 按 holding 的 interest_payment_freq/unit 和 principal_payment_freq/unit 生成支付日
    - 按 category_code 决定现金流类型
    - 用 yield_curve 贴现
    """

    def __init__(self, db: Session, curve: YieldCurve, scenario_code: str = 'BASE'):
        self.db = db
        self.curve = curve
        self.scenario_code = scenario_code
        self.report_date = date.today()

    def generate_all(self, company_id: int) -> Tuple[int, List[AssetCashflowRow]]:
        """生成某公司所有持仓的现金流"""
        rows = self.db.execute(
            text("""SELECT h.id, h.company_id, h.asset_code, h.face_value, h.cost_value, h.market_value,
                       h.coupon_rate, h.maturity_date, h.issue_date, h.interest_payment_freq,
                       h.interest_payment_unit, h.principal_payment_freq, h.principal_payment_unit,
                       h.duration_year, ac.category_code
                FROM ialm_asset_holding h
                LEFT JOIN ialm_asset_category ac ON ac.id = h.category_id AND ac.is_deleted = 0
                WHERE h.company_id = :cid AND h.is_deleted = 0"""),
            {"cid": company_id},
        ).fetchall()

        all_rows: List[AssetCashflowRow] = []
        for r in rows:
            all_rows.extend(self._generate_for_holding(r))
        return len(rows), all_rows

    def _generate_for_holding(self, h) -> List[AssetCashflowRow]:
        (hid, cid, acode, face, cost, market, coupon, maturity, issue,
         int_freq, int_unit, prin_freq, prin_unit, duration, cat_code) = h

        if not maturity or not face or float(face) <= 0:
            return []
        face = float(face)
        coupon = float(coupon or 0)
        out: List[AssetCashflowRow] = []
        cf_type = CATEGORY_CASHFLOW_TYPE.get(cat_code, 'COUPON')

        # 1. 现金/存款类：到期一次性还本+期间利息
        if cf_type in ('INTEREST',) and int_freq == 0 and prin_freq == 0:
            # 简化：1 年期，到期一次性本息
            prin_amt = face
            int_amt = face * coupon
            period_dt = maturity
            years = (maturity - self.report_date).days / 365.0
            if years <= 0:
                return []
            df = self.curve.discount_factor(years)
            out.append(AssetCashflowRow(
                holding_id=hid, company_id=cid, asset_code=acode,
                period_number=1, period_date=period_dt, period_year=round(years, 2),
                cashflow_type='INTEREST', amount=round(int_amt, 4),
                discount_factor=round(df, 6), present_value=round(int_amt * df, 4),
                scenario_code=self.scenario_code,
            ))
            out.append(AssetCashflowRow(
                holding_id=hid, company_id=cid, asset_code=acode,
                period_number=1, period_date=period_dt, period_year=round(years, 2),
                cashflow_type='PRINCIPAL', amount=round(prin_amt, 4),
                discount_factor=round(df, 6), present_value=round(prin_amt * df, 4),
                scenario_code=self.scenario_code,
            ))
            return out

        # 2. 债券类：按 int_freq/unit 生成息票，到期还本（外加最后一年利息）
        if cf_type in ('COUPON', 'DISTRIBUTION', 'RENTAL') and int_freq > 0:
            int_unit_years = UNIT_TO_YEARS.get(int_unit or 'YEAR', 1.0)
            interval_years = int_unit_years / max(int_freq, 1)
            # 期内现金流次数
            total_periods = max(1, int((maturity - self.report_date).days / 365.0 / interval_years))
            total_periods = min(total_periods, 100)  # 安全上限
            for n in range(1, int(total_periods) + 1):
                period_dt = self.report_date + timedelta(days=int(n * interval_years * 365))
                if period_dt > maturity:
                    period_dt = maturity
                years = (period_dt - self.report_date).days / 365.0
                if years <= 0:
                    continue
                df = self.curve.discount_factor(years)
                # 期间利息（按支付频率）
                per_period_coupon = face * coupon * interval_years
                if per_period_coupon > 0:
                    out.append(AssetCashflowRow(
                        holding_id=hid, company_id=cid, asset_code=acode,
                        period_number=n, period_date=period_dt, period_year=round(years, 2),
                        cashflow_type='COUPON', amount=round(per_period_coupon, 4),
                        discount_factor=round(df, 6), present_value=round(per_period_coupon * df, 4),
                        scenario_code=self.scenario_code,
                    ))
                # 本金摊销
                if prin_freq > 0 and n % max(int((prin_freq or 0) / max(int_freq, 1)), 1) == 0:
                    prin_per = face / max(int(total_periods), 1)
                    if prin_per > 0:
                        out.append(AssetCashflowRow(
                            holding_id=hid, company_id=cid, asset_code=acode,
                            period_number=n, period_date=period_dt, period_year=round(years, 2),
                            cashflow_type='PRINCIPAL', amount=round(prin_per, 4),
                            discount_factor=round(df, 6), present_value=round(prin_per * df, 4),
                            scenario_code=self.scenario_code,
                        ))
            # 最后一期剩余本金（如果 prin_freq == 0 即到期还本）
            if prin_freq == 0:
                last_years = (maturity - self.report_date).days / 365.0
                if last_years > 0:
                    last_df = self.curve.discount_factor(last_years)
                    out.append(AssetCashflowRow(
                        holding_id=hid, company_id=cid, asset_code=acode,
                        period_number=int(total_periods), period_date=maturity, period_year=round(last_years, 2),
                        cashflow_type='PRINCIPAL', amount=round(face, 4),
                        discount_factor=round(last_df, 6), present_value=round(face * last_df, 4),
                        scenario_code=self.scenario_code,
                    ))
            return out

        # 3. 股票类：按年付股息
        if cf_type == 'DIVIDEND':
            years_held = max(1, min(20, int((maturity - self.report_date).days / 365.0) if maturity else 10))
            for n in range(1, years_held + 1):
                period_dt = self.report_date + timedelta(days=n * 365)
                years = n
                df = self.curve.discount_factor(years)
                div = face * coupon  # 票面 × 股息率
                out.append(AssetCashflowRow(
                    holding_id=hid, company_id=cid, asset_code=acode,
                    period_number=n, period_date=period_dt, period_year=float(n),
                    cashflow_type='DIVIDEND', amount=round(div, 4),
                    discount_factor=round(df, 6), present_value=round(div * df, 4),
                    scenario_code=self.scenario_code,
                ))
            return out

        # 4. 衍生品类：到期一次性结算
        if cf_type == 'SETTLE':
            years = max(0.1, (maturity - self.report_date).days / 365.0)
            df = self.curve.discount_factor(years)
            settle_amt = face * (1 + coupon)  # 名义 + 收益
            out.append(AssetCashflowRow(
                holding_id=hid, company_id=cid, asset_code=acode,
                period_number=1, period_date=maturity, period_year=round(years, 2),
                cashflow_type='SETTLE', amount=round(settle_amt, 4),
                discount_factor=round(df, 6), present_value=round(settle_amt * df, 4),
                scenario_code=self.scenario_code,
            ))
            return out

        # 5. 默认：一次性 COUPON + PRINCIPAL（兜底）
        years = max(0.1, (maturity - self.report_date).days / 365.0) if maturity else 5
        df = self.curve.discount_factor(years)
        out.append(AssetCashflowRow(
            holding_id=hid, company_id=cid, asset_code=acode,
            period_number=1, period_date=maturity or self.report_date, period_year=round(years, 2),
            cashflow_type='COUPON', amount=round(face * coupon, 4),
            discount_factor=round(df, 6), present_value=round(face * coupon * df, 4),
            scenario_code=self.scenario_code,
        ))
        out.append(AssetCashflowRow(
            holding_id=hid, company_id=cid, asset_code=acode,
            period_number=1, period_date=maturity or self.report_date, period_year=round(years, 2),
            cashflow_type='PRINCIPAL', amount=round(face, 4),
            discount_factor=round(df, 6), present_value=round(face * df, 4),
            scenario_code=self.scenario_code,
        ))
        return out


# ════════════════════════════════════════════════════════════
# 负债端引擎
# ════════════════════════════════════════════════════════════
class LiabilityCashflowEngine:
    """
    负债现金流引擎
    - 保费流入 PREMIUM_IN（缴费期内）
    - 死亡赔付 CLAIM_OUT（按 mortality_table 的 qx）
    - 满期生存金 BENEFIT_OUT
    - 退保金 SURRENDER_OUT（按 lapse_rate，按 product_type 选不同率）
    - 费用 EXPENSE_OUT
    """

    def __init__(self, db: Session, curve: YieldCurve, scenario_code: str = 'BASE',
                 expense_rate: float = 0.08):
        self.db = db
        self.curve = curve
        self.scenario_code = scenario_code
        self.expense_rate = expense_rate
        self.report_date = date.today()

    def _load_mortality(self) -> Dict[Tuple[int, str], float]:
        """加载 (age, gender) -> qx 映射（混合 + 分性别混合使用）"""
        rows = self.db.execute(
            text("""SELECT p.age, p.qx, t.gender
                    FROM ialm_mortality_table_point p
                    JOIN ialm_mortality_table t ON t.id = p.table_id AND t.is_deleted = 0
                    WHERE p.is_deleted = 0
                      AND t.table_code IN ('CL3_MIXED', 'CL5_MIXED', 'CL1_MALE', 'CL2_FEMALE',
                                            'CL4_MALE', 'CL6_FEMALE')"""),
        ).fetchall()
        result: Dict[Tuple[int, str], float] = {}
        for age, qx, gender in rows:
            key = (age, gender)
            if key not in result or result[key] < float(qx):
                result[key] = float(qx)
        return result

    def _load_lapse_rates(self) -> Dict[int, float]:
        """加载 policy_year -> lapse_rate 全局默认（用于兜底）"""
        rows = self.db.execute(
            text("""SELECT rate_value FROM ialm_lapse_rate
                    WHERE is_deleted = 0 AND rate_code = 'LAPSE_GLOBAL' LIMIT 1"""),
        ).fetchone()
        return float(rows[0]) if rows else 0.05

    def _product_lapse_rate(self, product_type_id: int) -> float:
        """根据 product_type 取对应 lapse rate"""
        # 简化：基于 product_type_id 模数选不同率
        rates = self.db.execute(
            text("""SELECT rate_code, rate_value FROM ialm_lapse_rate WHERE is_deleted = 0"""),
        ).fetchall()
        # 根据 product_type_id 哈希选 rate_code
        order = ['LAPSE_ANNUITY', 'LAPSE_LIFE', 'LAPSE_GLOBAL', 'LAPSE_CRITICAL',
                 'LAPSE_HEALTH', 'LAPSE_HIGH_SURRENDER']
        idx = product_type_id % len(order) if product_type_id else 2
        target = order[idx]
        for code, val in rates:
            if code == target:
                return float(val)
        return 0.05

    def generate_all(self, company_id: int) -> Tuple[int, List[LiabilityCashflowRow]]:
        rows = self.db.execute(
            text("""SELECT pm.id, pm.company_id, pm.product_type_id, pm.sum_insured,
                       pm.annual_premium, pm.single_premium, pm.payment_period, pm.insurance_period,
                       pm.effective_date, pm.insured_age, pm.insured_gender,
                       pt.product_type_code AS category_code
                FROM ialm_policy_master pm
                LEFT JOIN ialm_product_category pt ON pt.id = pm.product_type_id AND pt.is_deleted = 0
                WHERE pm.company_id = :cid AND pm.is_deleted = 0"""),
            {"cid": company_id},
        ).fetchall()

        mortality = self._load_mortality()
        all_rows: List[LiabilityCashflowRow] = []
        for r in rows:
            all_rows.extend(self._generate_for_policy(r, mortality))
        return len(rows), all_rows

    def _generate_for_policy(self, p, mortality) -> List[LiabilityCashflowRow]:
        (pid, cid, prod_id, sum_ins, ann_prem, single_prem, pay_period, ins_period,
         eff_date, age, gender, cat_code) = p

        if not eff_date:
            eff_date = self.report_date
        if not ins_period or ins_period <= 0:
            ins_period = 20
        if not pay_period or pay_period <= 0:
            pay_period = min(ins_period, 10)
        if not sum_ins or float(sum_ins) <= 0:
            return []

        sum_ins = float(sum_ins)
        ann_prem = float(ann_prem or 0)
        single_prem = float(single_prem or 0)
        pay_period = int(pay_period)
        ins_period = int(ins_period)
        base_age = int(age or 30)
        gender = (gender or 'M').upper()
        lapse_rate = self._product_lapse_rate(prod_id or 0)
        out: List[LiabilityCashflowRow] = []

        # 1. 趸交保费（如有）
        if single_prem > 0:
            df = self.curve.discount_factor(0.01)
            out.append(LiabilityCashflowRow(
                company_id=cid, product_type_id=prod_id or 0, policy_id=pid,
                period_number=1, period_date=eff_date, period_year=0.01,
                cashflow_type='PREMIUM_IN', amount=round(single_prem, 4),
                discount_factor=round(df, 6), present_value=round(single_prem * df, 4),
                scenario_code=self.scenario_code,
            ))

        for y in range(1, ins_period + 1):
            period_dt = eff_date + timedelta(days=y * 365)
            years = (period_dt - self.report_date).days / 365.0
            if years < 0:
                years = 0
            df = self.curve.discount_factor(years)

            # 保费流入
            if y <= pay_period and ann_prem > 0:
                out.append(LiabilityCashflowRow(
                    company_id=cid, product_type_id=prod_id or 0, policy_id=pid,
                    period_number=y, period_date=period_dt, period_year=round(years, 2),
                    cashflow_type='PREMIUM_IN', amount=round(ann_prem, 4),
                    discount_factor=round(df, 6), present_value=round(ann_prem * df, 4),
                    scenario_code=self.scenario_code,
                ))

            # 死亡赔付（按 qx）
            qx = mortality.get((base_age + y - 1, gender), mortality.get((base_age + y - 1, 'MIXED'), 0.001))
            if sum_ins > 0 and qx > 0:
                claim = sum_ins * qx
                out.append(LiabilityCashflowRow(
                    company_id=cid, product_type_id=prod_id or 0, policy_id=pid,
                    period_number=y, period_date=period_dt, period_year=round(years, 2),
                    cashflow_type='CLAIM_OUT', amount=round(claim, 4),
                    discount_factor=round(df, 6), present_value=round(claim * df, 4),
                    scenario_code=self.scenario_code,
                ))

            # 满期生存金
            if y == ins_period:
                benefit = sum_ins * 1.05
                out.append(LiabilityCashflowRow(
                    company_id=cid, product_type_id=prod_id or 0, policy_id=pid,
                    period_number=y, period_date=period_dt, period_year=round(years, 2),
                    cashflow_type='BENEFIT_OUT', amount=round(benefit, 4),
                    discount_factor=round(df, 6), present_value=round(benefit * df, 4),
                    scenario_code=self.scenario_code,
                ))

            # 退保（中间年度）
            if pay_period < y < ins_period and ann_prem > 0:
                surrender = ann_prem * (ins_period - y) / ins_period * 1.0  # 现金价值近似
                surrender = surrender * lapse_rate
                if surrender > 0:
                    out.append(LiabilityCashflowRow(
                        company_id=cid, product_type_id=prod_id or 0, policy_id=pid,
                        period_number=y, period_date=period_dt, period_year=round(years, 2),
                        cashflow_type='SURRENDER_OUT', amount=round(surrender, 4),
                        discount_factor=round(df, 6), present_value=round(surrender * df, 4),
                        scenario_code=self.scenario_code,
                    ))

            # 费用（按 ann_prem 比例）
            if y <= pay_period and ann_prem > 0:
                exp = ann_prem * self.expense_rate
                out.append(LiabilityCashflowRow(
                    company_id=cid, product_type_id=prod_id or 0, policy_id=pid,
                    period_number=y, period_date=period_dt, period_year=round(years, 2),
                    cashflow_type='EXPENSE_OUT', amount=round(exp, 4),
                    discount_factor=round(df, 6), present_value=round(exp * df, 4),
                    scenario_code=self.scenario_code,
                ))

        return out


# ════════════════════════════════════════════════════════════
# 编排服务
# ════════════════════════════════════════════════════════════
class CashflowGenerationService:
    """现金流测算服务（编排 + 持久化）"""

    def __init__(self, db: Session, curve_code: str = 'CN-GB-2025'):
        self.db = db
        self.curve = self._load_curve(curve_code)

    def _load_curve(self, code: str) -> YieldCurve:
        row = self.db.execute(
            text("""SELECT id FROM ialm_yield_curve WHERE curve_code = :c AND is_deleted = 0 LIMIT 1"""),
            {"c": code},
        ).fetchone()
        if not row:
            return YieldCurve(curve_code=code, points=[])
        pts = self.db.execute(
            text("""SELECT tenor, rate FROM ialm_yield_curve_point
                    WHERE curve_id = :id ORDER BY tenor"""),
            {"id": row[0]},
        ).fetchall()
        return YieldCurve(curve_code=code, points=[(float(p[0]), float(p[1])) for p in pts])

    def regenerate_all(self, company_id: int, scenario_code: str = 'BASE') -> Dict:
        """重算某公司所有现金流（资产+负债）"""
        asset_engine = AssetCashflowEngine(self.db, self.curve, scenario_code)
        liab_engine = LiabilityCashflowEngine(self.db, self.curve, scenario_code)

        a_count, a_rows = asset_engine.generate_all(company_id)
        l_count, l_rows = liab_engine.generate_all(company_id)

        # 删除旧的 (company, scenario)
        self.db.execute(
            text("""DELETE FROM ialm_asset_cashflow
                    WHERE company_id = :cid AND scenario_code = :sc"""),
            {"cid": company_id, "sc": scenario_code},
        )
        self.db.execute(
            text("""DELETE FROM ialm_liability_cashflow
                    WHERE company_id = :cid AND scenario_code = :sc"""),
            {"cid": company_id, "sc": scenario_code},
        )

        # 批量插入资产
        if a_rows:
            self.db.execute(
                text("""INSERT INTO ialm_asset_cashflow
                       (holding_id, company_id, asset_code, period_number, period_date, period_year,
                        cashflow_type, amount, discount_factor, present_value, scenario_code)
                       VALUES (:holding_id, :company_id, :asset_code, :period_number, :period_date, :period_year,
                               :cashflow_type, :amount, :discount_factor, :present_value, :scenario_code)"""),
                [{"holding_id": r.holding_id, "company_id": r.company_id, "asset_code": r.asset_code,
                  "period_number": r.period_number, "period_date": r.period_date, "period_year": r.period_year,
                  "cashflow_type": r.cashflow_type, "amount": r.amount,
                  "discount_factor": r.discount_factor, "present_value": r.present_value,
                  "scenario_code": r.scenario_code} for r in a_rows],
            )

        # 批量插入负债
        if l_rows:
            self.db.execute(
                text("""INSERT INTO ialm_liability_cashflow
                       (company_id, product_type_id, policy_id, period_number, period_date, period_year,
                        cashflow_type, amount, discount_factor, present_value, scenario_code)
                       VALUES (:company_id, :product_type_id, :policy_id, :period_number, :period_date, :period_year,
                               :cashflow_type, :amount, :discount_factor, :present_value, :scenario_code)"""),
                [{"company_id": r.company_id, "product_type_id": r.product_type_id, "policy_id": r.policy_id,
                  "period_number": r.period_number, "period_date": r.period_date, "period_year": r.period_year,
                  "cashflow_type": r.cashflow_type, "amount": r.amount,
                  "discount_factor": r.discount_factor, "present_value": r.present_value,
                  "scenario_code": r.scenario_code} for r in l_rows],
            )

        self.db.commit()
        return {
            "asset_holdings_processed": a_count,
            "asset_cashflows_generated": len(a_rows),
            "liability_policies_processed": l_count,
            "liability_cashflows_generated": len(l_rows),
            "scenario_code": scenario_code,
            "curve_code": self.curve.curve_code,
        }

    def status(self, company_id: int) -> Dict:
        """引擎状态报告"""
        a_total = self.db.execute(
            text("""SELECT COUNT(*) AS cnt,
                          COUNT(DISTINCT scenario_code) AS scenarios,
                          MIN(period_date) AS first_date,
                          MAX(period_date) AS last_date,
                          SUM(present_value) AS total_pv
                   FROM ialm_asset_cashflow WHERE company_id = :cid"""),
            {"cid": company_id},
        ).fetchone()
        l_total = self.db.execute(
            text("""SELECT COUNT(*) AS cnt,
                          COUNT(DISTINCT scenario_code) AS scenarios,
                          MIN(period_date) AS first_date,
                          MAX(period_date) AS last_date,
                          SUM(present_value) AS total_pv
                   FROM ialm_liability_cashflow WHERE company_id = :cid"""),
            {"cid": company_id},
        ).fetchone()
        h_count = self.db.execute(
            text("""SELECT COUNT(*) FROM ialm_asset_holding
                    WHERE company_id = :cid AND is_deleted = 0"""),
            {"cid": company_id},
        ).scalar() or 0
        p_count = self.db.execute(
            text("""SELECT COUNT(*) FROM ialm_policy_master
                    WHERE company_id = :cid AND is_deleted = 0"""),
            {"cid": company_id},
        ).scalar() or 0
        return {
            "company_id": company_id,
            "curve_code": self.curve.curve_code,
            "curve_points": len(self.curve.points),
            "asset": {
                "holdings_total": h_count,
                "cashflows_total": int(a_total[0] or 0),
                "scenarios": int(a_total[1] or 0),
                "first_period": a_total[2].isoformat() if a_total[2] else None,
                "last_period": a_total[3].isoformat() if a_total[3] else None,
                "total_present_value": float(a_total[4] or 0),
            },
            "liability": {
                "policies_total": p_count,
                "cashflows_total": int(l_total[0] or 0),
                "scenarios": int(l_total[1] or 0),
                "first_period": l_total[2].isoformat() if l_total[2] else None,
                "last_period": l_total[3].isoformat() if l_total[3] else None,
                "total_present_value": float(l_total[4] or 0),
            },
        }