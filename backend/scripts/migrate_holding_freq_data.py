"""
根据实际资产分类设置合理的还息/还本频率。
"""
import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='ialm',
                      password='Ialm@2026', database='ialm_db', charset='utf8mb4')
cur = conn.cursor()

# 实际分类 code + 频率规则
# (category_code 前缀匹配, interest_freq, interest_unit, principal_freq, principal_unit)
RULES = [
    # 政府债/政策性金融债/银行金融债/企业债：年付息，到期还本
    ('BOND-GOVT',            1, 'YEAR',      0, 'YEAR'),
    ('BOND-CDB',             1, 'YEAR',      0, 'YEAR'),
    ('BOND-EXIMBANK',        1, 'YEAR',      0, 'YEAR'),
    ('BOND-BANK-ORDINARY',   1, 'YEAR',      0, 'YEAR'),
    ('BOND-BANK-T2',         1, 'YEAR',      0, 'YEAR'),
    ('BOND-CORP-AAA',        1, 'YEAR',      0, 'YEAR'),
    ('BOND-CORP-AA',         1, 'YEAR',      0, 'YEAR'),
    ('BOND-CORP-CITY',       1, 'YEAR',      0, 'YEAR'),
    # 基础设施债权/信托计划：季付息，到期还本
    ('ALTERNATIVE-INFRA',    1, 'QUARTER',   0, 'YEAR'),
    ('ALTERNATIVE-TRUST',    1, 'QUARTER',   0, 'YEAR'),
    # 现金：到期一次性还本
    ('CASH-DEPOSIT',         1, 'YEAR',      0, 'YEAR'),
    ('CASH-INTERBANK',       1, 'YEAR',      0, 'YEAR'),
    # 货币基金：净值变动，无息
    ('FUND-MONETARY',        0, 'YEAR',      0, 'YEAR'),
    # 其他基金：年分红
    ('FUND-ETF',             1, 'YEAR',      0, 'YEAR'),
    ('FUND-EQUITY',          1, 'YEAR',      0, 'YEAR'),
    ('FUND-BOND',            1, 'YEAR',      0, 'YEAR'),
    ('FUND-GOLD',            0, 'YEAR',      0, 'YEAR'),
    ('FUND-MIXED',           1, 'YEAR',      0, 'YEAR'),
    # 股票：年分红，不还本
    ('EQUITY-ASTOCK',        1, 'YEAR',      0, 'YEAR'),
    # 长期股权：年分红
    ('LT-EQUITY-ASSOC',      1, 'YEAR',      0, 'YEAR'),
    ('LT-EQUITY-SUBSID',     1, 'YEAR',      0, 'YEAR'),
    # 房地产：年付息
    ('REAL-ESTATE-OFFICE',   1, 'YEAR',      0, 'YEAR'),
    ('REAL-ESTATE-RETAIL',   1, 'YEAR',      0, 'YEAR'),
    # 其他
    ('OTHER-INV-AMC',        1, 'YEAR',      0, 'YEAR'),
    ('OTHER-INV-CD',         1, 'YEAR',      0, 'YEAR'),
    ('OTHER-INV-DERIV',      0, 'YEAR',      0, 'YEAR'),
]

updated = 0
for (prefix, i_freq, i_unit, p_freq, p_unit) in RULES:
    cur.execute("""
        UPDATE ialm_asset_holding h
        JOIN ialm_asset_category ac ON ac.id = h.category_id
        SET h.interest_payment_freq = %s,
            h.interest_payment_unit = %s,
            h.principal_payment_freq = %s,
            h.principal_payment_unit = %s
        WHERE ac.category_code = %s AND h.is_deleted = 0
    """, (i_freq, i_unit, p_freq, p_unit, prefix))
    updated += cur.rowcount

conn.commit()
print(f"✅ 已更新 {updated} 条持仓的还息/还本频率")

# 检查分布
cur.execute("""
    SELECT interest_payment_unit, COUNT(*) AS n
    FROM ialm_asset_holding WHERE is_deleted = 0
    GROUP BY interest_payment_unit ORDER BY n DESC
""")
print("\n=== 还息频率单位分布 ===")
for (u, n) in cur.fetchall():
    print(f"  {u:12s} {n} 条")

cur.execute("""
    SELECT ac.category_code, h.interest_payment_freq, h.interest_payment_unit,
           h.principal_payment_freq, h.principal_payment_unit, COUNT(*)
    FROM ialm_asset_holding h
    JOIN ialm_asset_category ac ON ac.id = h.category_id
    WHERE h.is_deleted = 0
    GROUP BY ac.category_code, h.interest_payment_freq, h.interest_payment_unit,
             h.principal_payment_freq, h.principal_payment_unit
    ORDER BY ac.category_code
""")
print("\n=== 按分类的频率分布 ===")
for row in cur.fetchall():
    print(f"  [{row[0]:22s}] 还息 {row[1]}/{row[2]:8s} 还本 {row[3]}/{row[4]} | {row[5]} 条")

conn.close()