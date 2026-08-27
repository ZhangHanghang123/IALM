"""
为投资组合页面生成完整 seed 数据（用 127.0.0.1 直连服务器本地 MySQL）
- ialm_portfolio_allocation：8 季度 × 4 种方法 × 10 大类资产
- ialm_performance_attribution：8 季度 Brinson 三效应分解（10 大类资产）
"""
import pymysql
import random
import json
from datetime import date
from decimal import Decimal

DB_CONFIG = dict(
    host='127.0.0.1', port=3306, user='ialm', password='Ialm@2026',
    database='ialm_db', charset='utf8mb4', autocommit=False,
)

COMPANY_ID = 4  # 新华保险

ASSET_BUCKETS = [
    (181, 'BOND', '债券投资', 0.045, 0.045, 0.45),
    (197, 'EQUITY', '权益类投资', 0.085, 0.180, 0.18),
    (201, 'FUND', '基金', 0.060, 0.110, 0.08),
    (177, 'CASH', '现金及现金等价物', 0.022, 0.005, 0.05),
    (208, 'ALTERNATIVE', '另类投资', 0.075, 0.090, 0.08),
    (215, 'REAL-ESTATE', '投资性房地产', 0.060, 0.080, 0.05),
    (212, 'LT-EQUITY', '长期股权投资', 0.080, 0.150, 0.06),
    (219, 'OTHER-INV', '其他投资', 0.050, 0.060, 0.03),
    (196, 'BOND-CONVERT', '可转换债券', 0.055, 0.090, 0.015),
    (220, 'OTHER-INV-DERIV', '金融衍生品', 0.025, 0.040, 0.005),
]

OPTIMIZATION_METHODS = [
    ('MARKOWITZ', 'Markowitz 均值-方差最优'),
    ('BLACK_LITTERMAN', 'Black-Litterman 配置'),
    ('EQUAL_WEIGHT', '等权基准'),
    ('STRATEGIC', '战略资产配置'),
]

PERIODS = [
    ('2022Q1', date(2022, 3, 31), date(2022, 1, 1), date(2022, 3, 31), 'QUARTERLY'),
    ('2022Q2', date(2022, 6, 30), date(2022, 4, 1), date(2022, 6, 30), 'QUARTERLY'),
    ('2022Q3', date(2022, 9, 30), date(2022, 7, 1), date(2022, 9, 30), 'QUARTERLY'),
    ('2022Q4', date(2022, 12, 31), date(2022, 10, 1), date(2022, 12, 31), 'QUARTERLY'),
    ('2023Q1', date(2023, 3, 31), date(2023, 1, 1), date(2023, 3, 31), 'QUARTERLY'),
    ('2023Q2', date(2023, 6, 30), date(2023, 4, 1), date(2023, 6, 30), 'QUARTERLY'),
    ('2023Q3', date(2023, 9, 30), date(2023, 7, 1), date(2023, 9, 30), 'QUARTERLY'),
    ('2023Q4', date(2023, 12, 31), date(2023, 10, 1), date(2023, 12, 31), 'QUARTERLY'),
]

BENCHMARK_CODE = 'XINHUA_LIFE_BENCH_2022'


def gen_method_weights(method, base_weights):
    if method == 'EQUAL_WEIGHT':
        return [round(1.0 / len(base_weights), 6)] * len(base_weights)
    elif method == 'STRATEGIC':
        return [round(w, 6) for w in base_weights]
    elif method == 'MARKOWITZ':
        factors = [0.5, -0.3, -0.2, 0.7, 0.0, 0.1, -0.1, 0.0, 0.0, 0.0]
        adjusted = [max(0.0, w * (1 + f)) for w, f in zip(base_weights, factors)]
        total = sum(adjusted)
        return [round(a / total, 6) for a in adjusted]
    elif method == 'BLACK_LITTERMAN':
        factors = [-0.1, 0.2, 0.1, -0.2, 0.2, 0.0, 0.1, 0.0, 0.1, 0.0]
        adjusted = [max(0.0, w * (1 + f)) for w, f in zip(base_weights, factors)]
        total = sum(adjusted)
        return [round(a / total, 6) for a in adjusted]
    return base_weights


def gen_brinson_effects(category_name, asset_code, base_w):
    random.seed(hash(category_name + asset_code) % 1000)
    bm_weight = base_w
    actual_weight = base_w * random.uniform(0.85, 1.15)
    alloc_eff = (actual_weight - bm_weight) * random.uniform(-0.02, 0.04)
    sel_eff = random.uniform(-0.015, 0.025)
    inter_eff = random.uniform(-0.008, 0.012)
    return (
        round(alloc_eff * 100, 4),
        round(sel_eff * 100, 4),
        round(inter_eff * 100, 4),
    )


def main():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as c:
        c.execute("DELETE FROM ialm_portfolio_allocation")
        c.execute("DELETE FROM ialm_performance_attribution")
        conn.commit()
        print("Cleared old portfolio data")

        alloc_count = 0
        for method_code, method_name in OPTIMIZATION_METHODS:
            for period_label, report_dt, _, _, _ in PERIODS:
                base_weights = [w for _, _, _, _, _, w in ASSET_BUCKETS]
                weights = gen_method_weights(method_code, base_weights)

                for (cat_id, code, name, exp_ret, exp_risk, _), w in zip(ASSET_BUCKETS, weights):
                    if w <= 0:
                        continue
                    sharpe = (exp_ret - 0.025) / exp_risk if exp_risk > 0 else 0
                    alloc_name = f"{period_label}_{method_name}_{name}"
                    c.execute("""INSERT INTO ialm_portfolio_allocation
                        (company_id, allocation_name, optimization_method, asset_code, asset_category_id,
                         weight, expected_return, expected_risk, report_date, sharpe_ratio,
                         extra_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (COMPANY_ID, alloc_name, method_code, code, cat_id,
                         round(w, 6), round(exp_ret, 4), round(exp_risk, 4), report_dt,
                         round(sharpe, 4),
                         json.dumps({"period": period_label, "method": method_code,
                                     "category_name": name}, ensure_ascii=False)))
                    alloc_count += 1
        conn.commit()
        print(f"Inserted {alloc_count} portfolio allocations")

        attr_count = 0
        for period_label, _, period_start, period_end, period_type in PERIODS:
            portfolio_code = f"XINHUA_LIFE_{period_label}_ACTUAL"
            for (cat_id, code, name, _, _, base_w) in ASSET_BUCKETS:
                alloc_eff, sel_eff, inter_eff = gen_brinson_effects(name, code, base_w)
                total_excess = round(alloc_eff + sel_eff + inter_eff, 4)
                c.execute("""INSERT INTO ialm_performance_attribution
                    (company_id, portfolio_code, benchmark_code, period_start, period_end, period_type,
                     asset_category_id, allocation_effect, selection_effect, interaction_effect,
                     total_excess, detail_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (COMPANY_ID, portfolio_code, BENCHMARK_CODE, period_start, period_end, period_type,
                     cat_id, alloc_eff, sel_eff, inter_eff, total_excess,
                     json.dumps({"asset_code": code, "category_name": name,
                                 "period_label": period_label,
                                 "breakdown": {"allocation": alloc_eff, "selection": sel_eff,
                                               "interaction": inter_eff}},
                                ensure_ascii=False)))
                attr_count += 1
        conn.commit()
        print(f"Inserted {attr_count} Brinson performance attributions")

    conn.close()
    print("\n=== Done ===")


if __name__ == '__main__':
    main()