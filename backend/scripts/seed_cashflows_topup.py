"""
补全 18 个没有现金流的持仓的现金流数据
- EQUITY-ASTOCK 股票 (12条): 5 年持有期，每年 DIVIDEND（按 coupon_rate），到期 PRINCIPAL=市值
- FUND-MONETARY 货币基金 (2条): 10 年，每年 INTEREST
- LT-EQUITY-SUBSID 长期股权 (2条): 5 年 DIVIDEND
- OTHER-INV-CD 同业存单 (1条): 0.4 年一次性 PRINCIPAL+COUPON
- OTHER-INV-DERIV 衍生品 (1条): 0.5 年一次性结算
"""
import pymysql
from datetime import datetime, timedelta

conn = pymysql.connect(host='127.0.0.1', port=3306, user='ialm',
                      password='Ialm@2026', database='ialm_db', charset='utf8mb4')
cur = conn.cursor()

cur.execute("""
SELECT h.id, h.asset_code, h.asset_name, ac.category_code,
       h.face_value, h.cost_value, h.market_value, h.coupon_rate,
       h.ytm, h.duration_year, h.issue_date, h.maturity_date
FROM ialm_asset_holding h
LEFT JOIN ialm_asset_category ac ON ac.id = h.category_id
LEFT JOIN ialm_asset_cashflow cf ON cf.holding_id = h.id AND cf.is_deleted = 0
WHERE h.company_id = 4 AND h.is_deleted = 0 AND cf.id IS NULL
ORDER BY h.id
""")
holdings = cur.fetchall()
print(f"待补全持仓：{len(holdings)} 条\n")

DISCOUNT_RATE = 0.030  # 3% 折现率

added_per_cat = {}
for (hid, acode, aname, ccat, face, cost, mv, coupon, ytm, dur,
     issue_dt, maturity_dt) in holdings:
    rows = []
    issue = issue_dt if isinstance(issue_dt, datetime) else datetime(2024, 1, 1)
    # 默认值：dur=0.5（半年）, face=10000
    face = float(face) if face else 0
    cost = float(cost) if cost else 0
    mv = float(mv) if mv else 0
    coupon = float(coupon) if coupon else 0
    ytm = float(ytm) if ytm else 0
    dur = float(dur) if dur else 0
    if not face or face == 0:
        face = cost or 10000.0
    if not mv or mv == 0:
        mv = face

    if ccat == 'EQUITY-ASTOCK':
        # 股票：5 年持有期，按 coupon_rate（股息率）每年发放 DIVIDEND，到期 PRICE=市值
        hold_years = 5
        div_rate = coupon if coupon else 0.04
        for yr in range(1, hold_years + 1):
            div_amt = face * div_rate
            cf_date = issue + timedelta(days=365 * yr)
            disc = 1.0 / ((1 + DISCOUNT_RATE) ** yr)
            rows.append((yr, yr, cf_date.strftime('%Y-%m-%d'), 'DIVIDEND', round(div_amt, 4), round(disc, 6),
                         round(div_amt * disc, 4)))
        # 第 5 年卖出（PRINCIPAL=市值）
        cf_date = issue + timedelta(days=365 * hold_years)
        disc = 1.0 / ((1 + DISCOUNT_RATE) ** hold_years)
        rows.append((hold_years, hold_years, cf_date.strftime('%Y-%m-%d'), 'PRINCIPAL',
                     round(mv, 4), round(disc, 6), round(mv * disc, 4)))

    elif ccat == 'FUND-MONETARY':
        # 货币基金：10 年，每年 INTEREST
        hold_years = 10
        int_rate = ytm if ytm else 0.025
        for yr in range(1, hold_years + 1):
            int_amt = face * int_rate
            cf_date = issue + timedelta(days=365 * yr)
            disc = 1.0 / ((1 + DISCOUNT_RATE) ** yr)
            rows.append((yr, yr, cf_date.strftime('%Y-%m-%d'), 'INTEREST',
                         round(int_amt, 4), round(disc, 6), round(int_amt * disc, 4)))
        # 10 年到期
        cf_date = issue + timedelta(days=365 * hold_years)
        disc = 1.0 / ((1 + DISCOUNT_RATE) ** hold_years)
        rows.append((hold_years, hold_years, cf_date.strftime('%Y-%m-%d'), 'PRINCIPAL',
                     round(face, 4), round(disc, 6), round(face * disc, 4)))

    elif ccat == 'LT-EQUITY-SUBSID':
        # 长期股权：5 年，每年 DIVIDEND（按 8%），到期 PRINCIPAL=面值
        hold_years = 5
        div_rate = 0.08
        for yr in range(1, hold_years + 1):
            div_amt = face * div_rate
            cf_date = issue + timedelta(days=365 * yr)
            disc = 1.0 / ((1 + DISCOUNT_RATE) ** yr)
            rows.append((yr, yr, cf_date.strftime('%Y-%m-%d'), 'DIVIDEND',
                         round(div_amt, 4), round(disc, 6), round(div_amt * disc, 4)))
        cf_date = issue + timedelta(days=365 * hold_years)
        disc = 1.0 / ((1 + DISCOUNT_RATE) ** hold_years)
        rows.append((hold_years, hold_years, cf_date.strftime('%Y-%m-%d'), 'PRINCIPAL',
                     round(face, 4), round(disc, 6), round(face * disc, 4)))

    elif ccat == 'OTHER-INV-CD':
        # 同业存单：0.4 年一次性（COUPON + PRINCIPAL）
        hold_years = 0.4
        int_rate = ytm if ytm else 0.025
        cf_date = issue + timedelta(days=int(365 * hold_years))
        disc = 1.0 / ((1 + DISCOUNT_RATE) ** hold_years)
        rows.append((1, hold_years, cf_date.strftime('%Y-%m-%d'), 'COUPON',
                     round(face * int_rate, 4), round(disc, 6), round(face * int_rate * disc, 4)))
        rows.append((1, hold_years, cf_date.strftime('%Y-%m-%d'), 'PRINCIPAL',
                     round(face, 4), round(disc, 6), round(face * disc, 4)))

    elif ccat == 'OTHER-INV-DERIV':
        # 衍生品：0.5 年一次性结算
        hold_years = 0.5
        disc = 1.0 / ((1 + DISCOUNT_RATE) ** hold_years)
        cf_date = issue + timedelta(days=int(365 * hold_years))
        settle_amt = mv - face  # 浮动盈亏
        rows.append((1, hold_years, cf_date.strftime('%Y-%m-%d'), 'SETTLE',
                     round(settle_amt, 4), round(disc, 6), round(settle_amt * disc, 4)))
        rows.append((1, hold_years, cf_date.strftime('%Y-%m-%d'), 'PRINCIPAL',
                     round(face, 4), round(disc, 6), round(face * disc, 4)))

    # 批量插入
    if rows:
        for (pnum, pyr, pdate, ctype, amt, df, pv) in rows:
            cur.execute("""
INSERT INTO ialm_asset_cashflow
                (holding_id, company_id, asset_code, period_number, period_date,
                 period_year, cashflow_type, amount, discount_factor, present_value,
                 scenario_code, is_deleted, created_at)
            VALUES (%s, 4, %s, %s, %s, %s, %s, %s, %s, %s, 'BASE', 0, NOW())
            """, (hid, acode, pnum, pdate, pyr, ctype, amt, df, pv))
        added_per_cat[ccat] = added_per_cat.get(ccat, 0) + 1

conn.commit()
print(f"✅ 补全完成：")
for cat, n in sorted(added_per_cat.items()):
    print(f"  {cat:20} {n} 条持仓")

# 重新统计
cur.execute("""
SELECT COUNT(DISTINCT holding_id) AS holdings_with_cf,
       COUNT(*) AS total_cf
FROM ialm_asset_cashflow
WHERE company_id = 4 AND is_deleted = 0
""")
print()
print("补全后状态：")
for r in cur.fetchall():
    print(f"  有现金流的持仓: {r[0]} | 总现金流记录: {r[1]}")
conn.close()