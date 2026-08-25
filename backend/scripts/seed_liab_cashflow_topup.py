"""
重建按保单的负债现金流（关联 ialm_policy_master，每张保单独立现金流）
- 每张保单第 1-N 年：每年 PREMIUM_IN（保费流入）
- 第 N 年：BENEFIT_OUT（保额给付）+ 部分保单 CLAIM_OUT（小额赔付）
- 期限单位：默认 YEAR（绝大多数寿险/年金/健康险按年）
"""
import pymysql
from datetime import datetime, timedelta
import sys

conn = pymysql.connect(host='127.0.0.1', port=3306, user='ialm',
                      password='Ialm@2026', database='ialm_db', charset='utf8mb4')
cur = conn.cursor()

# 1. 软删除现有负债现金流（按 product 聚合的）
cur.execute("UPDATE ialm_liability_cashflow SET is_deleted = 1 WHERE is_deleted = 0")
deleted = cur.rowcount
print(f"  ✅ 软删除旧的负债现金流 {deleted} 条")

# 2. 读所有保单
cur.execute("""SELECT id, policy_no, product_type_id, insurance_period, payment_period,
                      annual_premium, sum_insured, effective_date, insured_age, insured_gender
               FROM ialm_policy_master WHERE is_deleted = 0 ORDER BY id""")
policies = cur.fetchall()
print(f"  📋 待生成保单: {len(policies)} 条")

DISCOUNT_RATE = 0.030  # 3% 折现率
total_cf = 0
breakdown = {}  # 按类型统计

batch = []
for (pid, pno, ptid, ins_period, pay_period, premium, sum_insured, eff_date,
      insured_age, insured_gender) in policies:
    premium = float(premium) if premium else 0
    sum_insured = float(sum_insured) if sum_insured else 0
    ins_period = int(ins_period) if ins_period else 20
    pay_period = int(pay_period) if pay_period else ins_period
    insured_age = int(insured_age) if insured_age else 35
    if not eff_date:
        eff_date = datetime(2024, 1, 1)
    elif isinstance(eff_date, str):
        eff_date = datetime.strptime(eff_date, '%Y-%m-%d')

    # 期数 1 到保险期
    for yr in range(1, ins_period + 1):
        cf_date = eff_date + timedelta(days=365 * yr)
        disc = 1.0 / ((1 + DISCOUNT_RATE) ** yr)

        # 缴费期内：每年保费流入
        if yr <= pay_period and premium > 0:
            batch.append((pid, pno, yr, cf_date.strftime('%Y-%m-%d'), 'PREMIUM_IN',
                          round(premium, 4), round(disc, 6), round(premium * disc, 4)))
            total_cf += 1

        # 最后一年：给付（保额）
        if yr == ins_period and sum_insured > 0:
            batch.append((pid, pno, yr, cf_date.strftime('%Y-%m-%d'), 'BENEFIT_OUT',
                          round(sum_insured, 4), round(disc, 6), round(sum_insured * disc, 4)))
            total_cf += 1

        # 健康险/意外险（product_type_id 120-127 健康/意外险类）：随机小额赔付
        if ptid and 120 <= ptid <= 127 and yr % 5 == 0 and sum_insured > 0:
            claim_amt = sum_insured * 0.02  # 2% 保额作为小额赔付
            batch.append((pid, pno, yr, cf_date.strftime('%Y-%m-%d'), 'CLAIM_OUT',
                          round(claim_amt, 4), round(disc, 6), round(claim_amt * disc, 4)))
            total_cf += 1

# 3. 批量插入
if batch:
    cur.executemany("""
        INSERT INTO ialm_liability_cashflow
        (policy_id, product_type_id, period_number, period_count, period_unit,
         period_date, period_year, cashflow_type, amount, discount_factor, present_value,
         scenario_code, is_deleted, created_at)
        VALUES (%s, %s, %s, %s, 'YEAR', %s, %s, %s, %s, %s, %s, 'BASE', 0, NOW())
    """, [(b[0], 1, b[2], b[2], b[3], b[2], b[4], b[5], b[6], b[7]) for b in batch])

    # 统计 breakdown
    from collections import Counter
    breakdown = Counter(b[4] for b in batch)

conn.commit()
print(f"\n  ✅ 共生成 {total_cf} 条按保单的负债现金流")
print(f"  📊 类型分布:")
for ctype, n in sorted(breakdown.items()):
    print(f"     {ctype:15s} {n:5d} 条")

# 4. 验证
cur.execute("""SELECT COUNT(*) AS total, COUNT(DISTINCT policy_id) AS policies_with_cf
               FROM ialm_liability_cashflow WHERE is_deleted = 0""")
total, n_policies = cur.fetchone()
print(f"\n  📋 总数：{total} 条，{n_policies} 张保单有现金流")

cur.execute("""SELECT period_count, period_unit, COUNT(*)
               FROM ialm_liability_cashflow
               WHERE is_deleted = 0
               GROUP BY period_count, period_unit
               ORDER BY period_unit, period_count
               LIMIT 10""")
print(f"\n  📊 期限分布（前 10）:")
for (pc, pu, n) in cur.fetchall():
    print(f"     {pc:5.1f} {pu:10s} | {n} 条")

conn.close()