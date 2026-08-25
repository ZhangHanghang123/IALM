"""
IALM 业务演示数据种子脚本
使用 SQL 直接 INSERT（避免 ORM 字段名不一致）
"""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import pymysql
from urllib.parse import quote_plus
import os

# 从环境变量连接
DB_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('MYSQL_PORT', 3306))
DB_USER = os.getenv('MYSQL_USER', 'ialm')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Ialm@2026')
DB_NAME = os.getenv('MYSQL_DATABASE', 'ialm_db')


def get_conn():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME, charset='utf8mb4',
    )


def main():
    conn = get_conn()
    cur = conn.cursor()
    print(f"🔗 已连接 {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 60)

    # 1. 保险产品分类
    products = [
        ("LIFE-REGULAR", "普通寿险", 0, 1, "LIFE", "WHOLE_LIFE", "REGULAR"),
        ("LIFE-WHOLE", "终身寿险", 0, 2, "LIFE", "WHOLE_LIFE", "REGULAR"),
        ("LIFE-TERM", "定期寿险", 0, 2, "LIFE", "SHORT_TERM", "REGULAR"),
        ("LIFE-ANNUITY", "年金险", 0, 2, "ANNUNITY", "LONG_TERM", "SINGLE"),
        ("LIFE-HEALTH-CRITICAL", "重疾险", 0, 2, "HEALTH", "LONG_TERM", "REGULAR"),
        ("PROPERTY-AUTO", "车险", 0, 1, "ACCIDENT", "SHORT_TERM", "SINGLE"),
        ("PROPERTY-PROPERTY", "财产险", 0, 1, "ACCIDENT", "SHORT_TERM", "SINGLE"),
        ("PROPERTY-LIABILITY", "责任险", 0, 1, "ACCIDENT", "SHORT_TERM", "SINGLE"),
        ("HEALTH-MEDICAL", "医疗险", 0, 1, "HEALTH", "SHORT_TERM", "REGULAR"),
        ("REINSURANCE-LIFE", "寿险再保", 0, 1, "LIFE", "LONG_TERM", "REGULAR"),
    ]
    for code, name, parent_id, level, ins_type, dur_type, pay_type in products:
        cur.execute("SELECT id FROM ialm_product_category WHERE product_type_code = %s", (code,))
        if not cur.fetchone():
            cur.execute(
                """INSERT INTO ialm_product_category
                (product_type_code, product_type_name, parent_id, category_level,
                 insurance_type, duration_type, payment_type, is_risk_account, sort_order,
                 description, status, is_deleted, created_by, updated_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 0, '', 1, 0, 'system', 'system', NOW(), NOW())""",
                (code, name, parent_id, level, ins_type, dur_type, pay_type),
            )
    print(f"✅ 产品分类 {len(products)} 条")

    # 2. 资产分类
    categories = [
        ("CASH", "现金及银行存款", 0, 1, "CASH", 0.0, 0.0),
        ("DEPOSIT", "存放同业", 0, 1, "CASH", 0.2, 0.5),
        ("GOV-BOND", "政府债券", 0, 1, "BOND", 0.0, 7.0),
        ("FIN-BOND", "金融债券", 0, 1, "BOND", 0.1, 5.5),
        ("CORP-BOND", "企业债券", 0, 1, "BOND", 0.2, 4.5),
        ("STOCK", "股票", 0, 1, "EQUITY", 0.3, 3.0),
        ("FUND", "基金", 0, 1, "FUND", 0.25, 4.0),
        ("ALT-INVEST", "另类投资", 0, 1, "ALTERNATIVE", 0.4, 5.0),
    ]
    for code, name, parent_id, level, ctype, risk_w, dur in categories:
        cur.execute("SELECT id FROM ialm_asset_category WHERE category_code = %s", (code,))
        if not cur.fetchone():
            cur.execute(
                """INSERT INTO ialm_asset_category
                (category_code, category_name, parent_id, category_level,
                 category_type, risk_weight, duration_default,
                 status, is_deleted, created_by, updated_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s,
                        1, 0, 'system', 'system', NOW(), NOW())""",
                (code, name, parent_id, level, ctype, risk_w, dur),
            )
    print(f"✅ 资产分类 {len(categories)} 条")

    # 3. 收益率曲线（中债国债 + 信用债）
    curves = [
        ("CN-GB-2025", "中债国债收益率曲线", "SPOT", "CNY"),
        ("CN-FIN-2025", "中债金融债收益率曲线", "SPOT", "CNY"),
        ("CN-CORP-2025", "中债企业债收益率曲线", "SPOT", "CNY"),
        ("CN-CREDIT-AAA", "中债高等级信用债曲线", "SPOT", "CNY"),
    ]
    for code, name, ctype, ccy in curves:
        cur.execute("SELECT id FROM ialm_yield_curve WHERE curve_code = %s", (code,))
        row = cur.fetchone()
        if not row:
            cur.execute(
                """INSERT INTO ialm_yield_curve
                (curve_code, curve_name, curve_type, currency, data_source,
                 description, is_deleted, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'WIND', '', 0, NOW(), NOW())""",
                (code, name, ctype, ccy),
            )
            curve_id = cur.lastrowid
        else:
            curve_id = row[0]

        # 检查点位
        cur.execute("SELECT COUNT(*) FROM ialm_yield_curve_point WHERE curve_id = %s", (curve_id,))
        if cur.fetchone()[0] == 0:
            tenors = [(0.083, '3M'), (0.25, '6M'), (0.5, '1Y'), (1, '2Y'),
                      (3, '3Y'), (5, '5Y'), (7, '7Y'), (10, '10Y'),
                      (20, '20Y'), (30, '30Y')]
            base_rate = 0.025 if ctype == 'SPOT' and 'GB' in code else 0.030 if 'FIN' in code else 0.035
            for ty, label in tenors:
                rate = base_rate + 0.002 * ty + random.uniform(-0.001, 0.001)
                cur.execute(
                    """INSERT INTO ialm_yield_curve_point
                    (curve_id, curve_date, tenor, rate, created_at)
                    VALUES (%s, CURDATE(), %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE rate = VALUES(rate)""",
                    (curve_id, ty, round(rate, 4)),
                )
    print(f"✅ 收益率曲线 {len(curves)} 条 + 40 个点位")

    # 4. 资产持仓
    cur.execute("SELECT id FROM ialm_insurance_company WHERE is_deleted = 0")
    companies = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) FROM ialm_asset_holding WHERE is_deleted = 0")
    if cur.fetchone()[0] < 10:
        count = 0
        for cid in companies:
            for cat_code, cat_name, _, _, _, _, dur in categories[:5]:
                cur.execute("SELECT id FROM ialm_asset_holding WHERE company_id=%s AND category_code=%s AND is_deleted=0",
                            (cid, cat_code))
                if cur.fetchone():
                    continue
                book = random.randint(50000, 500000)
                cur.execute(
                    """INSERT INTO ialm_asset_holding
                    (company_id, category_code, holding_name, book_value, market_value,
                     coupon_rate, duration_years, maturity_date, rating, currency,
                     status, is_deleted, created_by, updated_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s,
                            DATE_ADD(CURDATE(), INTERVAL %s DAY), %s, 'CNY',
                            1, 0, 'system', 'system', NOW(), NOW())""",
                    (cid, cat_code, f"{cat_name} 持仓",
                     book, book, round(random.uniform(0.025, 0.045), 4),
                     round(random.uniform(2, 10), 2),
                     random.randint(365, 3650), random.choice(["AAA", "AA+", "AA", "AA-", "A+"])),
                )
                count += 1
        print(f"✅ 资产持仓 {count} 条")

    # 5. 保单
    cur.execute("SELECT COUNT(*) FROM ialm_policy_master WHERE is_deleted = 0")
    if cur.fetchone()[0] < 5:
        count = 0
        product_codes = [p[0] for p in products]
        for cid in companies:
            for i in range(3):
                cur.execute("SELECT id FROM ialm_policy_master WHERE company_id=%s AND is_deleted=0 LIMIT 1", (cid,))
                if cur.fetchone():
                    continue
                policy_no = f"P{cid}{i:04d}{random.randint(1000, 9999)}"
                cur.execute(
                    """INSERT INTO ialm_policy_master
                    (policy_no, company_id, product_code, insured_amount, premium,
                     policy_term, inception_date, maturity_date, status,
                     is_deleted, created_by, updated_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s,
                            DATE_SUB(CURDATE(), INTERVAL %s DAY),
                            DATE_ADD(CURDATE(), INTERVAL %s DAY), 'ACTIVE',
                            1, 0, 'system', 'system', NOW(), NOW())""",
                    (policy_no, cid, random.choice(product_codes),
                     random.randint(100, 5000) * 10000,  # 保额（万）
                     round(random.uniform(1, 50), 2) * 10000,  # 保费
                     random.choice([10, 20, 30, 50]),
                     random.randint(0, 1825), random.randint(365, 3650)),
                )
                count += 1
        print(f"✅ 保单 {count} 条")

    # 6. 风险偏好
    cur.execute("SELECT COUNT(*) FROM ialm_risk_preference WHERE is_deleted = 0")
    if cur.fetchone()[0] < len(companies):
        count = 0
        for cid in companies:
            cur.execute("SELECT id FROM ialm_risk_preference WHERE company_id=%s AND is_deleted=0", (cid,))
            if cur.fetchone():
                continue
            cur.execute(
                """INSERT INTO ialm_risk_preference
                (company_id, preference_level, max_drawdown, max_var, max_duration_gap,
                 target_solvency_ratio, target_lcr, effective_date, approved_by,
                 status, is_deleted, created_by, updated_by, created_at, updated_at)
                VALUES (%s, 'MODERATE', 0.10, 0.05, 1.0, 1.20, 1.05,
                        CURDATE(), 'admin', 1, 0, 'system', 'system', NOW(), NOW())""",
                (cid,),
            )
            count += 1
        print(f"✅ 风险偏好 {count} 条")

    # 7. 模型定义（14 项算法）
    models = [
        ("ALG-001", "期限匹配率测算", "DURATION", "P0", "5号规则"),
        ("ALG-002", "成本收益比测算", "COST_YIELD", "P0", "5号规则"),
        ("ALG-003", "现金流回正期测算", "CASHFLOW", "P0", "5号规则"),
        ("ALG-004", "久期与凸性测算", "DURATION", "P0", "5号规则"),
        ("ALG-005", "现金流贴现预测", "CASHFLOW", "P0", ""),
        ("ALG-006", "蒙特卡洛随机情景", "STRESS", "P0", "6号规则"),
        ("ALG-007", "多因子冲击传导", "STRESS", "P0", "6号规则"),
        ("ALG-008", "Markowitz 配置", "INVESTMENT", "P1", ""),
        ("ALG-009", "Black-Litterman", "INVESTMENT", "P1", ""),
        ("ALG-010", "Brinson 业绩归因", "INVESTMENT", "P2", ""),
        ("ALG-011", "VaR/CVaR 风险度量", "RISK", "P1", ""),
        ("ALG-012", "动态复制免疫", "RISK", "P2", ""),
        ("ALG-013", "再保险现金流影响", "CASHFLOW", "P2", ""),
        ("ALG-014", "久期匹配 ALM-DM", "INVESTMENT", "P1", ""),
    ]
    for code, name, cat, prio, reg in models:
        cur.execute("SELECT id FROM ialm_model_definition WHERE model_code = %s", (code,))
        if not cur.fetchone():
            cur.execute(
                """INSERT INTO ialm_model_definition
                (model_code, model_name, model_category, priority, regulatory_source,
                 description, formula_text, status, is_deleted, created_by, updated_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, '见算法详细设计文档',
                        1, 0, 'system', 'system', NOW(), NOW())""",
                (code, name, cat, prio, reg, f"{name}核心算法"),
            )
    print(f"✅ 模型定义 {len(models)} 条")

    conn.commit()
    cur.close()
    conn.close()
    print("=" * 60)
    print("🎉 演示数据种子完成")


if __name__ == "__main__":
    main()