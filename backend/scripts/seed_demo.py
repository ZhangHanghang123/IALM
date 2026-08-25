"""
IALM 业务演示数据种子脚本
填充保险产品分类 + 保单 + 持仓 + 收益率曲线 + 压力情景等
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, timedelta
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.security import hash_password

import random


def seed_all():
    s = SessionLocal()
    try:
        # 1. 产品分类
        products = [
            ("LIFE-REGULAR", "普通寿险", "", "LIFE"),
            ("LIFE-WHOLE", "终身寿险", "LIFE-REGULAR", "LIFE"),
            ("LIFE-TERM", "定期寿险", "LIFE-REGULAR", "LIFE"),
            ("LIFE-ANNUITY", "年金险", "LIFE-REGULAR", "LIFE"),
            ("LIFE-HEALTH-CRITICAL", "重疾险", "LIFE-REGULAR", "LIFE"),
            ("PROPERTY-AUTO", "车险", "", "PROPERTY"),
            ("PROPERTY-PROPERTY", "财产险", "", "PROPERTY"),
            ("PROPERTY-LIABILITY", "责任险", "", "PROPERTY"),
            ("HEALTH-MEDICAL", "医疗险", "", "HEALTH"),
            ("REINSURANCE-LIFE", "寿险再保", "", "REINSURANCE"),
        ]
        for code, name, parent, ptype in products:
            exists = s.execute(text("SELECT id FROM ialm_product_category WHERE category_code = :c"),
                                {"c": code}).fetchone()
            if not exists:
                s.execute(text("""INSERT INTO ialm_product_category
                    (category_code, category_name, parent_code, liability_type, status, is_deleted, created_by, updated_by, created_at, updated_at)
                    VALUES (:c, :n, :p, :t, 1, 0, 'system', 'system', NOW(), NOW())"""),
                    {"c": code, "n": name, "p": parent, "t": ptype})
        print(f"✅ 产品分类 {len(products)} 条")

        # 2. 资产分类
        categories = [
            ("CASH", "现金及银行存款", "", "LOW"),
            ("DEPOSIT", "存放同业", "", "LOW"),
            ("GOV-BOND", "政府债券", "", "LOW"),
            ("FIN-BOND", "金融债券", "", "LOW"),
            ("CORP-BOND", "企业债券", "", "MEDIUM"),
            ("STOCK", "股票", "", "HIGH"),
            ("FUND", "基金", "", "MEDIUM"),
            ("ALT-INVEST", "另类投资", "", "HIGH"),
        ]
        for code, name, parent, risk in categories:
            exists = s.execute(text("SELECT id FROM ialm_asset_category WHERE category_code = :c"),
                                {"c": code}).fetchone()
            if not exists:
                s.execute(text("""INSERT INTO ialm_asset_category
                    (category_code, category_name, parent_code, risk_level, status, is_deleted, created_by, updated_by, created_at, updated_at)
                    VALUES (:c, :n, :p, :r, 1, 0, 'system', 'system', NOW(), NOW())"""),
                    {"c": code, "n": name, "p": parent, "r": risk})
        print(f"✅ 资产分类 {len(categories)} 条")

        # 3. 资产持仓（每家公司 5 个）
        s.execute(text("SELECT id FROM ialm_asset_holding LIMIT 1")).fetchone() or None
        companies = s.execute(text("SELECT id FROM ialm_insurance_company WHERE is_deleted = 0")).fetchall()
        if not companies:
            print("⚠️ 无保险公司数据，跳过持仓")
        else:
            count = 0
            for cid_row in companies:
                cid = cid_row[0]
                for cat_code, cat_name, _, risk in categories[:5]:
                    book = random.randint(50000, 500000)
                    s.execute(text("""INSERT INTO ialm_asset_holding
                        (company_id, category_code, holding_name, book_value, market_value,
                         coupon_rate, duration_years, maturity_date, rating, currency,
                         status, is_deleted, created_by, updated_by, created_at, updated_at)
                        VALUES (:cid, :cc, :hn, :bv, :bv, :cr, :dy,
                                DATE_ADD(CURDATE(), INTERVAL :dt DAY), :rt, 'CNY',
                                1, 0, 'system', 'system', NOW(), NOW())"""),
                        {"cid": cid, "cc": cat_code, "hn": f"{cat_name} 持仓",
                         "bv": book, "cr": round(random.uniform(0.025, 0.045), 4),
                         "dy": round(random.uniform(2, 10), 2),
                         "dt": random.randint(365, 3650), "rt": random.choice(["AAA", "AA+", "AA", "AA-", "A+"])})
                    count += 1
            print(f"✅ 资产持仓 {count} 条")

        # 4. 保单（每家公司 3 个）
        if companies:
            count = 0
            for cid_row in companies:
                cid = cid_row[0]
                for i in range(3):
                    policy_no = f"P{cid}{i:04d}{random.randint(1000, 9999)}"
                    s.execute(text("""INSERT INTO ialm_policy_master
                        (policy_no, company_id, product_code, insured_amount, premium,
                         policy_term, inception_date, maturity_date, status,
                         is_deleted, created_by, updated_by, created_at, updated_at)
                        VALUES (:no, :cid, :pc, :ia, :pr, :pt,
                                DATE_SUB(CURDATE(), INTERVAL :sub DAY),
                                DATE_ADD(CURDATE(), INTERVAL :add DAY), 'ACTIVE',
                                1, 0, 'system', 'system', NOW(), NOW())"""),
                        {"no": policy_no, "cid": cid, "pc": random.choice([p[0] for p in products]),
                         "ia": random.randint(100, 5000), "pr": round(random.uniform(1, 50), 2),
                         "pt": random.choice([10, 20, 30, 50]),
                         "sub": random.randint(0, 1825), "add": random.randint(365, 3650)})
                    count += 1
            print(f"✅ 保单 {count} 条")

        # 5. 收益率曲线（中债国债 + 信用债）
        curves = [
            ("CN-GB-2025", "中债国债收益率曲线", "GOVERNMENT", "CNY"),
            ("CN-FIN-2025", "中债金融债收益率曲线", "FINANCIAL", "CNY"),
            ("CN-CORP-2025", "中债企业债收益率曲线", "CORPORATE", "CNY"),
            ("CN-CREDIT-AAA", "中债高等级信用债曲线", "CREDIT", "CNY"),
        ]
        for code, name, ctype, ccy in curves:
            exists = s.execute(text("SELECT id FROM ialm_yield_curve WHERE curve_code = :c"),
                                {"c": code}).fetchone()
            if not exists:
                cid = s.execute(text("""INSERT INTO ialm_yield_curve
                    (curve_code, curve_name, curve_type, currency, effective_date, source,
                     status, is_deleted, created_by, updated_by, created_at, updated_at)
                    VALUES (:c, :n, :t, :y, CURDATE(), '中债登', 1, 0, 'system', 'system', NOW(), NOW())"""),
                    {"c": code, "n": name, "t": ctype, "y": ccy}).lastrowid
                # 插入标准 10 个期限点位
                tenors = [(0.083, '3M'), (0.25, '6M'), (0.5, '1Y'), (1, '2Y'), (3, '3Y'), (5, '5Y'), (7, '7Y'), (10, '10Y'), (20, '20Y'), (30, '30Y')]
                base_rate = 0.025 if ctype == 'GOVERNMENT' else 0.030 if ctype == 'FINANCIAL' else 0.035
                for ty, label in tenors:
                    rate = base_rate + 0.002 * ty + random.uniform(-0.001, 0.001)
                    s.execute(text("""INSERT INTO ialm_yield_curve_point
                        (curve_id, tenor_years, tenor_label, rate, is_zero, is_par, is_forward,
                         status, is_deleted, created_by, updated_by, created_at, updated_at)
                        VALUES (:cid, :ty, :l, :r, 1, 0, 0, 1, 0, 'system', 'system', NOW(), NOW())"""),
                        {"cid": cid, "ty": ty, "l": label, "r": round(rate, 6)})
            print(f"✅ 收益率曲线 {len(curves)} 条")

        # 6. 风险偏好（每家公司一条）
        if companies:
            count = 0
            for cid_row in companies:
                cid = cid_row[0]
                exists = s.execute(text("SELECT id FROM ialm_risk_preference WHERE company_id = :cid AND is_deleted = 0"),
                                    {"cid": cid}).fetchone()
                if not exists:
                    s.execute(text("""INSERT INTO ialm_risk_preference
                        (company_id, preference_level, max_drawdown, max_var, max_duration_gap,
                         target_solvency_ratio, target_lcr, effective_date, approved_by,
                         status, is_deleted, created_by, updated_by, created_at, updated_at)
                        VALUES (:cid, 'MODERATE', 0.10, 0.05, 1.0, 1.20, 1.05,
                                CURDATE(), 'admin', 1, 0, 'system', 'system', NOW(), NOW())"""),
                        {"cid": cid})
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
            exists = s.execute(text("SELECT id FROM ialm_model_definition WHERE model_code = :c"),
                                {"c": code}).fetchone()
            if not exists:
                s.execute(text("""INSERT INTO ialm_model_definition
                    (model_code, model_name, model_category, priority, regulatory_source,
                     description, formula_text, status, is_deleted, created_by, updated_by, created_at, updated_at)
                    VALUES (:c, :n, :cat, :p, :r, :d, '见算法详细设计文档',
                            1, 0, 'system', 'system', NOW(), NOW())"""),
                    {"c": code, "n": name, "cat": cat, "p": prio, "r": reg, "d": f"{name}核心算法"})
        print(f"✅ 模型定义 {len(models)} 条")

        s.commit()
        print("=" * 60)
        print("🎉 演示数据种子完成")

    except Exception as e:
        s.rollback()
        print(f"❌ 失败: {e}")
        raise
    finally:
        s.close()


if __name__ == "__main__":
    seed_all()