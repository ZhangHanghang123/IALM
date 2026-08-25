"""查看 ialm_db 当前数据状态"""
import pymysql

conn = pymysql.connect(
    host='127.0.0.1', port=3306,
    user='ialm', password='Ialm@2026',
    database='ialm_db', charset='utf8mb4',
)
cur = conn.cursor()

print("=== 各表记录数 ===")
tables = [
    'ialm_insurance_company', 'ialm_product_category', 'ialm_policy_master',
    'ialm_asset_category', 'ialm_asset_holding', 'ialm_asset_cashflow',
    'ialm_liability_cashflow', 'ialm_reserve', 'ialm_mortality_table',
    'ialm_mortality_table_point', 'ialm_lapse_rate', 'ialm_actuarial_assumption',
    'ialm_yield_curve', 'ialm_yield_curve_point', 'ialm_risk_preference',
    'ialm_model_definition',
]
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t} WHERE is_deleted = 0 OR is_deleted IS NULL")
        print(f"  {t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"  {t}: ERROR {e}")

print("\n=== 所有公司 ===")
cur.execute("SELECT id, company_code, company_name, company_short FROM ialm_insurance_company WHERE is_deleted = 0 ORDER BY id")
for r in cur.fetchall():
    print(" ", r)

print("\n=== 资产分类 ===")
cur.execute("SELECT id, category_code, category_name, parent_id, category_type FROM ialm_asset_category WHERE is_deleted = 0 ORDER BY id")
for r in cur.fetchall():
    print(" ", r)

print("\n=== 产品分类 ===")
cur.execute("SELECT id, product_type_code, product_type_name, parent_id, insurance_type FROM ialm_product_category WHERE is_deleted = 0 ORDER BY id")
for r in cur.fetchall():
    print(" ", r)

print("\n=== 部分资产持仓 ===")
cur.execute("SELECT id, asset_code, asset_name, company_id, category_id, face_value, cost_value, market_value FROM ialm_asset_holding WHERE is_deleted = 0 ORDER BY id LIMIT 10")
for r in cur.fetchall():
    print(" ", r)

print("\n=== 部分保单 ===")
cur.execute("SELECT id, policy_no, company_id, product_type_id, sum_insured, annual_premium FROM ialm_policy_master WHERE is_deleted = 0 ORDER BY id LIMIT 10")
for r in cur.fetchall():
    print(" ", r)

conn.close()
