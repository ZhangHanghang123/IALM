"""把现有 ialm_asset_cashflow / ialm_liability_cashflow 的 period_year 转换为 period_count + period_unit"""
import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='ialm',
                      password='Ialm@2026', database='ialm_db', charset='utf8mb4')
cur = conn.cursor()

def convert(year_value):
    """根据 period_year 数值，返回 (period_count, period_unit)"""
    if year_value is None or year_value == 0:
        return 0, 'YEAR'
    if year_value >= 1:
        return float(year_value), 'YEAR'
    # < 1 年：转换为月
    months = round(year_value * 12)
    if months < 1:
        months = 1
    return float(months), 'MONTH'

updated_asset = 0
cur.execute("SELECT id, period_year FROM ialm_asset_cashflow WHERE is_deleted = 0")
for (cid, py) in cur.fetchall():
    py = float(py) if py else 0
    pc, pu = convert(py)
    cur.execute("UPDATE ialm_asset_cashflow SET period_count=%s, period_unit=%s WHERE id=%s",
                (pc, pu, cid))
    updated_asset += 1

updated_liab = 0
cur.execute("SELECT id, period_year FROM ialm_liability_cashflow WHERE is_deleted = 0")
for (cid, py) in cur.fetchall():
    py = float(py) if py else 0
    pc, pu = convert(py)
    cur.execute("UPDATE ialm_liability_cashflow SET period_count=%s, period_unit=%s WHERE id=%s",
                (pc, pu, cid))
    updated_liab += 1

conn.commit()
print(f"✅ 资产现金流: {updated_asset} 条已迁移")
print(f"✅ 负债现金流: {updated_liab} 条已迁移")

# 检查迁移结果
cur.execute("""SELECT period_unit, COUNT(*) AS n,
                       ROUND(MIN(period_count), 2) AS min_count,
                       ROUND(MAX(period_count), 2) AS max_count
                FROM ialm_asset_cashflow
                WHERE is_deleted = 0 GROUP BY period_unit ORDER BY period_unit""")
print("\n=== 资产现金流期限分布 ===")
for r in cur.fetchall():
    print(f"  {r[0]:12s} {r[1]:4d} 条 | 期限范围 {r[2]:.2f} - {r[3]:.2f}")

cur.execute("""SELECT period_unit, COUNT(*) AS n,
                       ROUND(MIN(period_count), 2) AS min_count,
                       ROUND(MAX(period_count), 2) AS max_count
                FROM ialm_liability_cashflow
                WHERE is_deleted = 0 GROUP BY period_unit ORDER BY period_unit""")
print("\n=== 负债现金流期限分布 ===")
for r in cur.fetchall():
    print(f"  {r[0]:12s} {r[1]:4d} 条 | 期限范围 {r[2]:.2f} - {r[3]:.2f}")

conn.close()