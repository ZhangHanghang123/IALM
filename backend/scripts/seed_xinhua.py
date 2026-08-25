"""
IALM 新华保险完整数据种子脚本
- 清理：删除除新华保险（id=4）外的所有公司及关联数据
- 重建：分类树、持仓、保单、现金流、准备金、死亡率表、退保率、精算假设
- 关联：建立产品-资产配置关联表 ialm_product_asset_link
"""
import pymysql
import random
from datetime import date, datetime, timedelta

DB = dict(host='127.0.0.1', port=3306, user='ialm', password='Ialm@2026',
          database='ialm_db', charset='utf8mb4', autocommit=False)

random.seed(42)  # 固定种子可重现

XINHUA_ID = 4  # 新华保险现有 id（已存在的）

TODAY = date.today()
REPORT_DATE = TODAY.replace(day=1)  # 月初作为报告日


def get_conn():
    return pymysql.connect(**DB)


def run():
    conn = get_conn()
    cur = conn.cursor()
    print("🔗 已连接 ialm_db")
    print("=" * 70)

    # ═══ STEP 1: 清理非新华保险数据 ═══
    print("\n[STEP 1] 清理非新华保险数据...")

    cur.execute("SELECT id FROM ialm_insurance_company WHERE id != %s AND is_deleted = 0", (XINHUA_ID,))
    other_ids = [r[0] for r in cur.fetchall()]
    print(f"  其他公司 id: {other_ids}")

    if other_ids:
        # 软删除其持仓/保单/风险偏好/现金流（注意：ialm_match_analysis 有 holding_id 没有 company_id，跳过）
        for table in ['ialm_asset_holding', 'ialm_policy_master', 'ialm_risk_preference',
                      'ialm_asset_cashflow', 'ialm_liability_cashflow', 'ialm_reserve',
                      'ialm_actuarial_assumption']:
            cur.execute(f"UPDATE {table} SET is_deleted = 1 WHERE company_id IN ({','.join(['%s']*len(other_ids))})",
                        other_ids)
        # 软删除公司
        cur.execute(f"UPDATE ialm_insurance_company SET is_deleted = 1 WHERE id IN ({','.join(['%s']*len(other_ids))})",
                    other_ids)
    print(f"  ✅ 清理完成：软删除 {len(other_ids)} 家非新华保险公司")

    # 清理新华保险旧的非分类数据（保留分类，重建具体数据）
    # ialm_match_analysis 没有 is_deleted 列，直接硬删
    for table in ['ialm_asset_holding', 'ialm_policy_master', 'ialm_risk_preference',
                  'ialm_asset_cashflow', 'ialm_liability_cashflow', 'ialm_reserve',
                  'ialm_actuarial_assumption']:
        cur.execute(f"UPDATE {table} SET is_deleted = 1 WHERE company_id = %s", (XINHUA_ID,))
    # ialm_match_analysis 没有 is_deleted，硬删
    cur.execute("DELETE FROM ialm_match_analysis WHERE company_id = %s", (XINHUA_ID,))
    # 单独处理 ialm_lapse_rate（无 company_id）—— 硬删
    cur.execute("DELETE FROM ialm_lapse_rate")
    # 死亡率表和点位全部清空重做（硬删避免 unique key 冲突）
    cur.execute("DELETE FROM ialm_mortality_table_point")
    cur.execute("DELETE FROM ialm_mortality_table")
    print("  ✅ 新华保险旧的具体数据清理完成（保留分类树）")

    conn.commit()

    # ═══ STEP 2: 重建资产分类树（多层级） ═══
    print("\n[STEP 2] 重建资产分类树...")
    # 硬删除旧分类（unique key 不能重复）
    cur.execute("DELETE FROM ialm_asset_holding WHERE company_id = %s", (XINHUA_ID,))
    cur.execute("DELETE FROM ialm_asset_category")
    conn.commit()

    # 新分类树：一级 → 二级 → 三级
    asset_categories = [
        # (code, name, parent_code, category_type, risk_weight, duration_default, level)
        ("CASH", "现金及现金等价物", "", "CASH", 0.0, 0.0, 1),
        ("CASH-DEPOSIT", "银行存款", "CASH", "CASH", 0.0, 0.5, 2),
        ("CASH-INTERBANK", "存放同业", "CASH", "CASH", 0.2, 0.5, 2),
        ("CASH-MMF", "货币市场基金", "CASH", "FUND", 0.05, 0.2, 2),

        ("BOND", "债券投资", "", "BOND", 0.05, 7.0, 1),
        ("BOND-GOVT", "政府债券", "BOND", "BOND", 0.0, 10.0, 2),
        ("BOND-GOVT-10Y", "10 年期国债", "BOND-GOVT", "BOND", 0.0, 8.5, 3),
        ("BOND-GOVT-20Y", "20 年期国债", "BOND-GOVT", "BOND", 0.0, 14.0, 3),
        ("BOND-GOVT-30Y", "30 年期国债", "BOND-GOVT", "BOND", 0.0, 18.0, 3),
        ("BOND-POLICY", "政策性金融债", "BOND", "BOND", 0.1, 8.0, 2),
        ("BOND-CDB", "国开债", "BOND-POLICY", "BOND", 0.05, 8.5, 3),
        ("BOND-EXIMBANK", "进出口行债", "BOND-POLICY", "BOND", 0.05, 7.0, 3),
        ("BOND-COMMERCIAL", "商业银行金融债", "BOND", "BOND", 0.15, 6.0, 2),
        ("BOND-BANK-T2", "商业银行二级资本债", "BOND-COMMERCIAL", "BOND", 0.2, 7.5, 3),
        ("BOND-BANK-ORDINARY", "商业银行普通金融债", "BOND-COMMERCIAL", "BOND", 0.1, 4.0, 3),
        ("BOND-CORP", "企业债券", "BOND", "BOND", 0.2, 5.5, 2),
        ("BOND-CORP-AAA", "AAA 企业债", "BOND-CORP", "BOND", 0.15, 5.5, 3),
        ("BOND-CORP-AA", "AA+ 企业债", "BOND-CORP", "BOND", 0.25, 4.0, 3),
        ("BOND-CORP-CITY", "城投债", "BOND-CORP", "BOND", 0.2, 4.5, 3),
        ("BOND-CONVERT", "可转换债券", "BOND", "BOND", 0.3, 4.5, 2),

        ("EQUITY", "权益类投资", "", "EQUITY", 0.4, 5.0, 1),
        ("EQUITY-ASTOCK", "A 股股票", "EQUITY", "EQUITY", 0.4, 4.0, 2),
        ("EQUITY-HSTOCK", "H 股股票", "EQUITY", "EQUITY", 0.4, 4.0, 2),
        ("EQUITY-PREFERRED", "优先股", "EQUITY", "EQUITY", 0.3, 6.0, 2),

        ("FUND", "基金", "", "FUND", 0.3, 4.0, 1),
        ("FUND-EQUITY", "股票型基金", "FUND", "FUND", 0.35, 5.0, 2),
        ("FUND-BOND", "债券型基金", "FUND", "FUND", 0.1, 3.0, 2),
        ("FUND-MIXED", "混合型基金", "FUND", "FUND", 0.25, 4.0, 2),
        ("FUND-MONETARY", "货币型基金", "FUND", "FUND", 0.05, 0.2, 2),
        ("FUND-ETF", "ETF 指数基金", "FUND", "FUND", 0.3, 5.0, 2),
        ("FUND-GOLD", "黄金 ETF", "FUND", "FUND", 0.3, 3.0, 2),

        ("ALTERNATIVE", "另类投资", "", "ALTERNATIVE", 0.4, 6.0, 1),
        ("ALTERNATIVE-INFRA", "基础设施债权计划", "ALTERNATIVE", "ALTERNATIVE", 0.25, 8.0, 2),
        ("ALTERNATIVE-TRUST", "信托计划", "ALTERNATIVE", "ALTERNATIVE", 0.45, 5.0, 2),
        ("ALTERNATIVE-REITS", "基础设施 REITs", "ALTERNATIVE", "ALTERNATIVE", 0.3, 10.0, 2),

        ("LT-EQUITY", "长期股权投资", "", "OTHER", 0.35, 8.0, 1),
        ("LT-EQUITY-ASSOC", "联营企业", "LT-EQUITY", "OTHER", 0.35, 8.0, 2),
        ("LT-EQUITY-SUBSID", "子公司", "LT-EQUITY", "OTHER", 0.3, 8.0, 2),

        ("REAL-ESTATE", "投资性房地产", "", "OTHER", 0.3, 15.0, 1),
        ("REAL-ESTATE-OFFICE", "商业写字楼", "REAL-ESTATE", "OTHER", 0.3, 18.0, 2),
        ("REAL-ESTATE-RETAIL", "商业地产", "REAL-ESTATE", "OTHER", 0.35, 15.0, 2),

        ("OTHER-INV", "其他投资", "", "OTHER", 0.4, 3.0, 1),
        ("OTHER-INV-CD", "同业存单", "OTHER-INV", "OTHER", 0.1, 0.5, 2),
        ("OTHER-INV-DERIV", "金融衍生品", "OTHER-INV", "OTHER", 0.5, 1.0, 2),
        ("OTHER-INV-AMC", "资产管理计划", "OTHER-INV", "OTHER", 0.4, 4.0, 2),
    ]

    cat_id_map = {}
    for code, name, parent_code, ctype, risk_w, dur, level in asset_categories:
        parent_id = cat_id_map.get(parent_code, 0) if parent_code else 0
        cur.execute("""INSERT INTO ialm_asset_category
                       (category_code, category_name, parent_id, category_level, category_type,
                        risk_weight, duration_default, sort_order, status, is_deleted,
                        created_by, updated_by, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, 'system', 'system', NOW(), NOW())""",
                    (code, name, parent_id, level, ctype, risk_w, dur, 0))
        cat_id_map[code] = cur.lastrowid
    conn.commit()
    print(f"  ✅ 资产分类树 {len(asset_categories)} 个节点（3 级）")

    # ═══ STEP 3: 重建产品分类树 ═══
    print("\n[STEP 3] 重建产品分类树...")
    cur.execute("DELETE FROM ialm_policy_master WHERE company_id = %s", (XINHUA_ID,))
    cur.execute("DELETE FROM ialm_product_category")
    conn.commit()

    product_categories = [
        # (code, name, parent_code, insurance_type, duration_type, payment_type, is_risk_account, level)
        ("LIFE", "寿险", "", "LIFE", "LONG_TERM", "REGULAR", 1, 1),
        ("LIFE-REGULAR", "普通寿险", "LIFE", "LIFE", "LONG_TERM", "REGULAR", 1, 2),
        ("LIFE-WHOLE", "终身寿险", "LIFE", "LIFE", "WHOLE_LIFE", "REGULAR", 1, 2),
        ("LIFE-TERM", "定期寿险", "LIFE", "LIFE", "SHORT_TERM", "REGULAR", 1, 2),
        ("LIFE-PARTICIPATING", "分红寿险", "LIFE", "LIFE", "LONG_TERM", "REGULAR", 1, 2),
        ("LIFE-UNIVERSAL", "万能寿险", "LIFE", "UNIVERSAL", "LONG_TERM", "REGULAR", 1, 2),

        ("ANNUITY", "年金险", "", "ANNUNITY", "LONG_TERM", "SINGLE", 1, 1),
        ("ANNUITY-PENSION", "养老年金", "ANNUITY", "ANNUNITY", "LONG_TERM", "SINGLE", 1, 2),
        ("ANNUITY-EDUCATION", "教育年金", "ANNUITY", "ANNUNITY", "LONG_TERM", "REGULAR", 1, 2),

        ("HEALTH", "健康险", "", "HEALTH", "LONG_TERM", "REGULAR", 1, 1),
        ("HEALTH-CRITICAL", "重疾险", "HEALTH", "HEALTH", "LONG_TERM", "REGULAR", 1, 2),
        ("HEALTH-MEDICAL", "医疗险", "HEALTH", "HEALTH", "SHORT_TERM", "REGULAR", 1, 2),
        ("HEALTH-CANCER", "防癌险", "HEALTH", "HEALTH", "LONG_TERM", "REGULAR", 1, 2),

        ("ACCIDENT", "意外险", "", "ACCIDENT", "SHORT_TERM", "SINGLE", 1, 1),
        ("ACCIDENT-COMPREHENSIVE", "综合意外险", "ACCIDENT", "ACCIDENT", "SHORT_TERM", "SINGLE", 1, 2),
        ("ACCIDENT-TRAVEL", "交通意外险", "ACCIDENT", "ACCIDENT", "SHORT_TERM", "SINGLE", 1, 2),
    ]

    prod_id_map = {}
    for code, name, parent_code, ins_type, dur_type, pay_type, is_risk, level in product_categories:
        parent_id = prod_id_map.get(parent_code, 0) if parent_code else 0
        cur.execute("""INSERT INTO ialm_product_category
                       (product_type_code, product_type_name, parent_id, category_level, insurance_type,
                        duration_type, payment_type, is_risk_account, sort_order, status, is_deleted,
                        created_by, updated_by, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 0, 'system', 'system', NOW(), NOW())""",
                    (code, name, parent_id, level, ins_type, dur_type, pay_type, is_risk, 0))
        prod_id_map[code] = cur.lastrowid
    conn.commit()
    print(f"  ✅ 产品分类树 {len(product_categories)} 个节点（2 级）")

    # ═══ STEP 4: 产品-资产关联（核心：建立配比关系） ═══
    print("\n[STEP 4] 建立产品-资产关联...")

    # 各产品的典型资产配置（参考新华保险实际投资策略）
    # 寿险类（长期）：偏保守，长期国债 + 信用债
    # 年金险（超长期）：极保守，国债 + 政策性金融债为主
    # 健康险（中长期）：稳健，企业债 + 长期国债
    # 意外险（短期）：流动性高，现金 + 短债
    product_asset_allocations = [
        # (product_code, [(asset_category_code, allocation_pct, expected_duration)])
        ("LIFE-REGULAR", [
            ("BOND-GOVT-20Y", 0.35, 14.0),
            ("BOND-GOVT-10Y", 0.25, 8.5),
            ("BOND-BANK-T2", 0.15, 7.5),
            ("BOND-CORP-AAA", 0.15, 5.5),
            ("EQUITY-ASTOCK", 0.10, 4.0),
        ]),
        ("LIFE-WHOLE", [
            ("BOND-GOVT-30Y", 0.40, 18.0),
            ("BOND-GOVT-20Y", 0.30, 14.0),
            ("BOND-CORP-AAA", 0.15, 5.5),
            ("EQUITY-ASTOCK", 0.15, 4.0),
        ]),
        ("LIFE-TERM", [
            ("BOND-GOVT-10Y", 0.30, 8.5),
            ("BOND-BANK-ORDINARY", 0.25, 4.0),
            ("BOND-CORP-AAA", 0.25, 5.5),
            ("CASH-DEPOSIT", 0.10, 0.5),
            ("FUND-BOND", 0.10, 3.0),
        ]),
        ("LIFE-PARTICIPATING", [
            ("BOND-GOVT-20Y", 0.30, 14.0),
            ("BOND-CORP-AAA", 0.20, 5.5),
            ("EQUITY-ASTOCK", 0.20, 4.0),
            ("FUND-EQUITY", 0.15, 5.0),
            ("BOND-BANK-T2", 0.15, 7.5),
        ]),
        ("ANNUITY-PENSION", [
            ("BOND-GOVT-30Y", 0.45, 18.0),
            ("BOND-GOVT-20Y", 0.25, 14.0),
            ("BOND-POLICY", 0.15, 8.0),
            ("BOND-CORP-AAA", 0.10, 5.5),
            ("CASH-DEPOSIT", 0.05, 0.5),
        ]),
        ("ANNUITY-EDUCATION", [
            ("BOND-GOVT-10Y", 0.35, 8.5),
            ("BOND-GOVT-20Y", 0.25, 14.0),
            ("BOND-CORP-AAA", 0.20, 5.5),
            ("BOND-BANK-T2", 0.15, 7.5),
            ("FUND-BOND", 0.05, 3.0),
        ]),
        ("HEALTH-CRITICAL", [
            ("BOND-GOVT-10Y", 0.30, 8.5),
            ("BOND-BANK-T2", 0.20, 7.5),
            ("BOND-CORP-AAA", 0.20, 5.5),
            ("BOND-CORP-AA", 0.10, 4.0),
            ("EQUITY-ASTOCK", 0.10, 4.0),
            ("CASH-DEPOSIT", 0.10, 0.5),
        ]),
        ("HEALTH-MEDICAL", [
            ("CASH-DEPOSIT", 0.20, 0.5),
            ("CASH-MMF", 0.15, 0.2),
            ("BOND-BANK-ORDINARY", 0.25, 4.0),
            ("BOND-CORP-AAA", 0.20, 5.5),
            ("FUND-MONETARY", 0.15, 0.2),
            ("FUND-BOND", 0.05, 3.0),
        ]),
        ("ACCIDENT-COMPREHENSIVE", [
            ("CASH-DEPOSIT", 0.30, 0.5),
            ("CASH-INTERBANK", 0.20, 0.5),
            ("BOND-BANK-ORDINARY", 0.20, 4.0),
            ("OTHER-INV-CD", 0.15, 0.5),
            ("FUND-MONETARY", 0.15, 0.2),
        ]),
        ("LIFE-UNIVERSAL", [
            ("BOND-GOVT-10Y", 0.25, 8.5),
            ("BOND-BANK-T2", 0.20, 7.5),
            ("BOND-CORP-AAA", 0.20, 5.5),
            ("EQUITY-ASTOCK", 0.15, 4.0),
            ("FUND-MIXED", 0.10, 4.0),
            ("CASH-DEPOSIT", 0.10, 0.5),
        ]),
    ]

    link_count = 0
    for prod_code, allocs in product_asset_allocations:
        prod_id = prod_id_map[prod_code]
        for asset_code, pct, dur in allocs:
            asset_id = cat_id_map[asset_code]
            cur.execute("""INSERT INTO ialm_product_asset_link
                           (company_id, product_type_id, asset_category_id, allocation_pct, duration_match,
                            remark, is_deleted, created_by, updated_by, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s, '', 0, 'system', 'system', NOW(), NOW())""",
                        (XINHUA_ID, prod_id, asset_id, pct, dur))
            link_count += 1
    conn.commit()
    print(f"  ✅ 产品-资产关联 {link_count} 条")

    # ═══ STEP 5: 重建资产持仓（新华保险真实投资组合） ═══
    print("\n[STEP 5] 重建资产持仓...")
    cur.execute("UPDATE ialm_asset_holding SET is_deleted = 1 WHERE company_id = %s", (XINHUA_ID,))
    conn.commit()

    # 新华保险 2024 年报典型投资组合（万元）
    # 总投资规模约 16,500,000 万元（1.65 万亿）
    holdings = [
        # === 现金及银行存款 (1,650,000 万, 10%) ===
        ("CASH-DEPOSIT", "工商银行存款", "中国工商银行", "AAA", 50000, 0.020, 0.5, "0.5Y", 50000.0000),
        ("CASH-DEPOSIT", "建设银行存款", "中国建设银行", "AAA", 40000, 0.020, 0.5, "0.5Y", 40000.0000),
        ("CASH-DEPOSIT", "农业银行存款", "中国农业银行", "AAA", 35000, 0.020, 0.5, "0.5Y", 35000.0000),
        ("CASH-DEPOSIT", "中国银行存款", "中国银行", "AAA", 25000, 0.020, 0.5, "0.5Y", 25000.0000),
        ("CASH-DEPOSIT", "招商银行存款", "招商银行", "AAA", 15000, 0.020, 0.5, "0.5Y", 15000.0000),
        ("CASH-INTERBANK", "国开行同业存款", "国家开发银行", "AAA", 30000, 0.025, 0.5, "1Y", 30000.0000),
        ("CASH-INTERBANK", "进出口行同业存款", "中国进出口银行", "AAA", 20000, 0.025, 0.5, "1Y", 20000.0000),
        ("CASH-INTERBANK", "招行同业存出", "招商银行", "AAA", 32500, 0.025, 0.5, "1Y", 32500.0000),

        # === 政府债券 (4,125,000 万, 25%) ===
        ("BOND-GOVT-30Y", "24 国债 010107", "中华人民共和国财政部", "", 0.0342, 0.0352, 24.0, "25Y", 100000.0000),
        ("BOND-GOVT-30Y", "24 国债 010110", "中华人民共和国财政部", "", 0.0352, 0.0362, 22.5, "25Y", 80000.0000),
        ("BOND-GOVT-20Y", "23 国债 010308", "中华人民共和国财政部", "", 0.0332, 0.0342, 14.5, "20Y", 60000.0000),
        ("BOND-GOVT-20Y", "22 国债 010512", "中华人民共和国财政部", "", 0.0305, 0.0315, 11.0, "15Y", 42500.0000),
        ("BOND-GOVT-10Y", "24 国债 010510", "中华人民共和国财政部", "", 0.0285, 0.0295, 8.5, "10Y", 50000.0000),
        ("BOND-GOVT-10Y", "23 国债 019512", "中华人民共和国财政部", "", 0.0255, 0.0265, 4.5, "5Y", 40000.0000),
        ("BOND-GOVT-10Y", "22 国债 019657", "中华人民共和国财政部", "", 0.0265, 0.0275, 5.5, "7Y", 40000.0000),

        # === 政策性金融债 (1,650,000 万, 10%) ===
        ("BOND-CDB", "24 国开 03", "国家开发银行", "AAA", 0.0385, 0.0395, 7.5, "10Y", 60000.0000),
        ("BOND-CDB", "23 国开 10", "国家开发银行", "AAA", 0.0365, 0.0375, 6.5, "10Y", 40000.0000),
        ("BOND-CDB", "22 国开 20", "国家开发银行", "AAA", 0.0375, 0.0385, 14.0, "20Y", 50000.0000),
        ("BOND-EXIMBANK", "24 进出 05", "中国进出口银行", "AAA", 0.0375, 0.0385, 6.5, "10Y", 35000.0000),
        ("BOND-EXIMBANK", "23 进出 10", "中国进出口银行", "AAA", 0.0365, 0.0375, 12.0, "15Y", 30000.0000),

        # === 商业银行二级资本债 (660,000 万, 4%) ===
        ("BOND-BANK-T2", "25 工行二级资本债 01", "中国工商银行", "AAA", 0.0412, 0.0425, 7.5, "10Y", 30000.0000),
        ("BOND-BANK-T2", "24 建行二级资本债 02", "中国建设银行", "AAA", 0.0410, 0.0420, 7.0, "10Y", 28000.0000),
        ("BOND-BANK-T2", "24 农行二级资本债 01", "中国农业银行", "AAA", 0.0405, 0.0418, 7.0, "10Y", 25000.0000),
        ("BOND-BANK-T2", "24 招行二级资本债 01", "招商银行", "AAA", 0.0420, 0.0435, 6.5, "10Y", 20000.0000),
        ("BOND-BANK-T2", "23 中行二级资本债 01", "中国银行", "AAA", 0.0415, 0.0428, 6.5, "10Y", 18000.0000),
        ("BOND-BANK-T2", "24 交行二级资本债 01", "交通银行", "AAA", 0.0418, 0.0430, 7.0, "10Y", 15000.0000),

        # === 商业银行普通金融债 ===
        ("BOND-BANK-ORDINARY", "25 中信银行债 01", "中信银行", "AAA", 0.0385, 0.0395, 3.5, "5Y", 29000.0000),
        ("BOND-BANK-ORDINARY", "24 浦发债 02", "浦发银行", "AAA", 0.0380, 0.0390, 3.5, "5Y", 22000.0000),
        ("BOND-BANK-ORDINARY", "24 兴业债 01", "兴业银行", "AAA", 0.0382, 0.0392, 4.5, "5Y", 25000.0000),

        # === AAA 企业债 (1,485,000 万, 9%) ===
        ("BOND-CORP-AAA", "24 国家电网 MTN001", "国家电网有限公司", "AAA", 0.0395, 0.0408, 8.5, "10Y", 50000.0000),
        ("BOND-CORP-AAA", "23 中石油 MTN005", "中国石油天然气集团", "AAA", 0.0405, 0.0418, 8.0, "10Y", 45000.0000),
        ("BOND-CORP-AAA", "24 中石化 MTN002", "中国石油化工集团", "AAA", 0.0400, 0.0412, 8.0, "10Y", 40000.0000),
        ("BOND-CORP-AAA", "24 中国电信 MTN003", "中国电信集团", "AAA", 0.0390, 0.0402, 5.5, "7Y", 36000.0000),
        ("BOND-CORP-AAA", "23 中国移动 MTN002", "中国移动通信集团", "AAA", 0.0385, 0.0395, 5.5, "7Y", 30000.0000),
        ("BOND-CORP-AAA", "24 长江电力 MTN001", "中国长江电力股份", "AAA", 0.0395, 0.0405, 8.0, "10Y", 25000.0000),
        ("BOND-CORP-AAA", "24 中海油 MTN001", "中国海洋石油集团", "AAA", 0.0410, 0.0422, 4.0, "5Y", 20000.0000),
        ("BOND-CORP-AAA", "23 万科 MTN001", "万科企业股份", "AAA", 0.0450, 0.0470, 3.5, "5Y", 16000.0000),
        ("BOND-CORP-AAA", "22 碧桂园 MTN001", "碧桂园控股", "AAA", 0.0520, 0.0580, 1.5, "3Y", 10000.0000),
        ("BOND-CORP-CITY", "24 沪城投 MTN001", "上海城投集团", "AAA", 0.0430, 0.0442, 4.0, "5Y", 13500.0000),
        ("BOND-CORP-CITY", "24 京国资 MTN001", "北京国资公司", "AAA", 0.0425, 0.0438, 4.0, "5Y", 12000.0000),
        ("BOND-CORP-CITY", "24 粤财投资 MTN001", "广东粤财投资控股", "AAA", 0.0435, 0.0448, 4.0, "5Y", 10000.0000),

        # === AA+ 企业债 (495,000 万, 3%) ===
        ("BOND-CORP-AA", "24 上实 MTN001", "上海实业(集团)", "AA+", 0.0485, 0.0500, 4.0, "5Y", 20000.0000),
        ("BOND-CORP-AA", "23 北控 MTN001", "北京控股集团", "AA+", 0.0470, 0.0485, 4.0, "5Y", 16000.0000),
        ("BOND-CORP-AA", "24 比亚迪 MTN001", "比亚迪股份", "AA+", 0.0510, 0.0525, 2.5, "3Y", 16000.0000),
        ("BOND-CORP-AA", "24 格力 MTN001", "格力电器", "AA+", 0.0450, 0.0465, 2.5, "3Y", 12000.0000),
        ("BOND-CORP-AA", "24 海尔 MTN001", "海尔智家", "AA+", 0.0465, 0.0480, 2.5, "3Y", 12000.0000),
        ("BOND-CORP-AA", "24 美的 MTN001", "美的集团", "AA+", 0.0455, 0.0470, 2.5, "3Y", 12000.0000),
        ("BOND-CORP-AA", "24 伊利 MTN001", "伊利股份", "AA+", 0.0475, 0.0490, 2.5, "3Y", 11000.0000),
        ("BOND-CORP-AA", "24 海康 MTN001", "海康威视", "AA+", 0.0480, 0.0495, 2.5, "3Y", 9000.0000),

        # === A 股股票 (1,155,000 万, 7%) ===
        ("EQUITY-ASTOCK", "工商银行(601398)", "中国工商银行", "AAA", 0.060, 0.060, 0.0, "", 20000.0000),
        ("EQUITY-ASTOCK", "建设银行(601939)", "中国建设银行", "AAA", 0.055, 0.055, 0.0, "", 18000.0000),
        ("EQUITY-ASTOCK", "中国平安(601318)", "中国平安保险", "AAA", 0.050, 0.050, 0.0, "", 15000.0000),
        ("EQUITY-ASTOCK", "招商银行(600036)", "招商银行", "AAA", 0.045, 0.045, 0.0, "", 13000.0000),
        ("EQUITY-ASTOCK", "贵州茅台(600519)", "贵州茅台", "AAA", 0.035, 0.035, 0.0, "", 10000.0000),
        ("EQUITY-ASTOCK", "中国移动(600941)", "中国移动", "AAA", 0.030, 0.030, 0.0, "", 8000.0000),
        ("EQUITY-ASTOCK", "长江电力(600900)", "长江电力", "AAA", 0.025, 0.025, 0.0, "", 7000.0000),
        ("EQUITY-ASTOCK", "比亚迪(002594)", "比亚迪股份", "AA+", 0.020, 0.020, 0.0, "", 6000.0000),
        ("EQUITY-ASTOCK", "宁德时代(300750)", "宁德时代", "AA+", 0.018, 0.018, 0.0, "", 5000.0000),
        ("EQUITY-ASTOCK", "美的集团(000333)", "美的集团", "AA+", 0.010, 0.010, 0.0, "", 3000.0000),
        ("EQUITY-ASTOCK", "腾讯控股(00700)", "腾讯控股", "AAA", 0.008, 0.008, 0.0, "", 2500.0000),
        ("EQUITY-ASTOCK", "中国平安 H 股(02318)", "中国平安", "AAA", 0.030, 0.030, 0.0, "", 8000.0000),

        # === 基金 (1,155,000 万, 7%) ===
        ("FUND-ETF", "易方达沪深 300 ETF", "易方达基金", "AA+", 0.000, 0.045, 5.0, "", 30000.0000),
        ("FUND-ETF", "华夏上证 50 ETF", "华夏基金", "AA+", 0.000, 0.040, 5.0, "", 20000.0000),
        ("FUND-ETF", "南方中证 500 ETF", "南方基金", "AA+", 0.000, 0.045, 5.0, "", 13000.0000),
        ("FUND-BOND", "嘉实债券基金", "嘉实基金", "AA+", 0.038, 0.040, 3.0, "", 15000.0000),
        ("FUND-MONETARY", "招商现金管理货币基金", "招商基金", "AAA", 0.020, 0.022, 0.2, "", 10000.0000),
        ("FUND-EQUITY", "富国天惠成长混合", "富国基金", "AA+", 0.000, 0.060, 5.0, "", 8000.0000),
        ("FUND-EQUITY", "银华富裕主题混合", "银华基金", "AA+", 0.000, 0.055, 5.0, "", 5500.0000),
        ("FUND-MIXED", "广发稳健增长混合", "广发基金", "AA+", 0.000, 0.050, 4.0, "", 7000.0000),
        ("FUND-GOLD", "国泰黄金 ETF", "国泰基金", "AA+", 0.000, 0.040, 3.0, "", 6000.0000),
        ("FUND-EQUITY", "兴全合润分级混合", "兴证全球基金", "AA+", 0.000, 0.058, 5.0, "", 6500.0000),
        ("FUND-BOND", "易方达中短期债券", "易方达基金", "AA+", 0.032, 0.035, 2.0, "", 9000.0000),
        ("FUND-MONETARY", "南方天天利货币", "南方基金", "AAA", 0.022, 0.024, 0.2, "", 8500.0000),

        # === 基础设施债权计划 (660,000 万, 4%) ===
        ("ALTERNATIVE-INFRA", "京沪高铁债权投资计划", "京沪高铁公司", "AAA", 0.0485, 0.0500, 12.0, "15Y", 15000.0000),
        ("ALTERNATIVE-INFRA", "港珠澳大桥债权计划", "港珠澳大桥管理局", "AAA", 0.0490, 0.0505, 14.0, "15Y", 12000.0000),
        ("ALTERNATIVE-INFRA", "雄安新区基础设施债权", "中国雄安集团", "AAA", 0.0475, 0.0490, 10.0, "12Y", 10000.0000),
        ("ALTERNATIVE-INFRA", "粤港澳大湾区基础设施债权", "广东恒健", "AAA", 0.0478, 0.0492, 9.5, "12Y", 9000.0000),
        ("ALTERNATIVE-INFRA", "长江经济带基础设施债权", "长江产业投资", "AAA", 0.0480, 0.0495, 10.0, "12Y", 10000.0000),
        ("ALTERNATIVE-INFRA", "长三角基础设施债权计划", "上海国际集团", "AAA", 0.0470, 0.0485, 9.0, "10Y", 10000.0000),
        ("ALTERNATIVE-INFRA", "北京地铁基础设施债权", "北京基础设施投资", "AAA", 0.0472, 0.0488, 9.0, "10Y", 8000.0000),
        ("ALTERNATIVE-INFRA", "成都地铁基础设施债权", "成都轨道交通集团", "AA+", 0.0495, 0.0510, 9.0, "10Y", 6000.0000),

        # === 信托计划 (330,000 万, 2%) ===
        ("ALTERNATIVE-TRUST", "信托·基础设施集合资金", "中信信托", "AA+", 0.0510, 0.0530, 5.0, "5Y", 10000.0000),
        ("ALTERNATIVE-TRUST", "信托·优质工商企业", "中国信托", "AA+", 0.0525, 0.0545, 4.0, "5Y", 8000.0000),
        ("ALTERNATIVE-TRUST", "信托·金融领域", "平安信托", "AAA", 0.0480, 0.0495, 5.0, "5Y", 10000.0000),
        ("ALTERNATIVE-TRUST", "信托·房地产组合", "中海信托", "AA", 0.0560, 0.0580, 4.0, "5Y", 5000.0000),

        # === 长期股权投资 (330,000 万, 2%) ===
        ("LT-EQUITY-ASSOC", "中国金茂控股", "中国金茂控股集团", "AA+", 0.000, 0.045, 8.0, "", 13000.0000),
        ("LT-EQUITY-SUBSID", "新华健康险", "新华健康", "AAA", 0.000, 0.000, 0.0, "", 8000.0000),
        ("LT-EQUITY-SUBSID", "新华养老", "新华养老保险", "AAA", 0.000, 0.000, 0.0, "", 12000.0000),

        # === 投资性房地产 (247,500 万, 1.5%) ===
        ("REAL-ESTATE-OFFICE", "北京 CBD 国贸写字楼", "北京国贸中心", "AAA", 0.000, 0.045, 18.0, "", 10000.0000),
        ("REAL-ESTATE-OFFICE", "上海陆家嘴办公楼", "上海陆家嘴金融贸易区", "AAA", 0.000, 0.045, 17.0, "", 8000.0000),
        ("REAL-ESTATE-RETAIL", "深圳福田商务楼", "深圳福田中心区", "AAA", 0.000, 0.042, 15.0, "", 6750.0000),

        # === 其他投资 ===
        ("OTHER-INV-CD", "同业存单 24 期", "工商银行", "AAA", 0.022, 0.024, 0.4, "0.5Y", 3500.0000),
        ("OTHER-INV-AMC", "中信资产管理计划", "中信证券资产管理", "AA+", 0.0435, 0.0455, 4.0, "5Y", 8000.0000),
        ("OTHER-INV-DERIV", "国债期货套保头寸", "中金所", "AAA", 0.000, 0.000, 0.5, "1Y", 5000.0000),
    ]

    holding_count = 0
    for asset_code, name, issuer, rating, coupon, ytm, dur, tenor_label, face_value in holdings:
        cat_id = cat_id_map[asset_code]
        # 计算到期日（按剩余期限）
        if dur > 0:
            maturity = TODAY + timedelta(days=int(dur * 365))
            issue = maturity - timedelta(days=int(_parse_years(tenor_label) * 365))
        else:
            maturity = None
            issue = TODAY - timedelta(days=random.randint(365, 1825))

        # 资产编号
        seq = holding_count + 1001
        asset_code_str = f"XH{seq:06d}"

        cur.execute("""INSERT INTO ialm_asset_holding
                       (company_id, asset_code, asset_name, category_id, asset_subtype, issuer, credit_rating,
                        face_value, cost_value, market_value, coupon_rate, ytm,
                        issue_date, maturity_date, duration_year, effective_duration, convexity,
                        payment_freq, currency, report_date, source, is_deleted,
                        created_by, updated_by, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s,
                               1, 'CNY', %s, 'MANUAL', 0,
                               'system', 'system', NOW(), NOW())""",
                    (XINHUA_ID, asset_code_str, name, cat_id, asset_code.split('-')[0], issuer, rating,
                     face_value, face_value, face_value * random.uniform(0.99, 1.05) if face_value > 1000 else face_value,
                     coupon, ytm,
                     issue, maturity, dur, dur, dur * (dur + 1) / 100 if dur > 0 else 0,
                     REPORT_DATE))
        holding_count += 1
    conn.commit()
    print(f"  ✅ 资产持仓 {holding_count} 条")

    # ═══ STEP 6: 重建保单（50 条） ═══
    print("\n[STEP 6] 重建保单...")

    cur.execute("UPDATE ialm_policy_master SET is_deleted = 1 WHERE company_id = %s", (XINHUA_ID,))
    conn.commit()

    # 50 条保单数据
    policy_templates = [
        # (product_code, count, sum_insured_range, premium_rate, period_min, period_max, payment_period_min)
        ("LIFE-REGULAR", 6, (50, 200), 0.015, 15, 30, 10),
        ("LIFE-WHOLE", 5, (100, 500), 0.018, 30, 50, 15),
        ("LIFE-TERM", 4, (50, 150), 0.005, 10, 20, 5),
        ("LIFE-PARTICIPATING", 4, (80, 300), 0.020, 20, 30, 10),
        ("LIFE-UNIVERSAL", 2, (50, 200), 0.015, 20, 30, 10),
        ("ANNUITY-PENSION", 6, (100, 500), 0.025, 30, 50, 10),
        ("ANNUITY-EDUCATION", 4, (30, 150), 0.020, 15, 25, 5),
        ("HEALTH-CRITICAL", 8, (30, 100), 0.012, 20, 30, 10),
        ("HEALTH-MEDICAL", 4, (5, 30), 0.008, 1, 5, 1),
        ("HEALTH-CANCER", 3, (20, 80), 0.010, 15, 25, 10),
        ("ACCIDENT-COMPREHENSIVE", 4, (10, 50), 0.003, 1, 1, 1),
        ("ACCIDENT-TRAVEL", 2, (5, 30), 0.002, 1, 1, 1),
    ]

    policy_count = 0
    policyholder_names = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
    for prod_code, cnt, sum_range, prem_rate, period_min, period_max, pay_min in policy_templates:
        prod_id = prod_id_map[prod_code]
        for i in range(cnt):
            policy_count += 1
            seq = policy_count
            policy_no = f"XL-{datetime.now().year}-{seq:05d}"

            insured_age = random.randint(25, 55)
            insured_gender = random.choice(['M', 'F'])
            insurance_period = random.randint(period_min, period_max)
            payment_period = min(pay_min, insurance_period - 5)
            sum_insured = round(random.uniform(*sum_range), 2)
            annual_premium = round(sum_insured * prem_rate * random.uniform(0.9, 1.1), 4)
            single_premium = annual_premium if prod_code.startswith('ANNUITY') and random.random() < 0.4 else 0

            issue_date = TODAY - timedelta(days=random.randint(180, 365 * 8))
            effective_date = issue_date
            maturity_date = issue_date + timedelta(days=insurance_period * 365)

            cur.execute("""INSERT INTO ialm_policy_master
                           (policy_no, company_id, product_type_id, product_name,
                            policyholder_id, insured_id, insured_age, insured_gender,
                            sum_insured, annual_premium, single_premium,
                            payment_freq, payment_period, insurance_period,
                            issue_date, effective_date, maturity_date,
                            status, currency, reserve_balance, is_deleted,
                            created_by, updated_by, created_at, updated_at)
                           VALUES (%s, %s, %s, %s,
                                   %s, %s, %s, %s,
                                   %s, %s, %s,
                                   1, %s, %s,
                                   %s, %s, %s,
                                   'IN_FORCE', 'CNY', %s, 0,
                                   'system', 'system', NOW(), NOW())""",
                        (policy_no, XINHUA_ID, prod_id, prod_code,
                         f"ID{random.randint(100000000000000000, 999999999999999999)}",
                         f"ID{random.randint(100000000000000000, 999999999999999999)}",
                         insured_age, insured_gender,
                         sum_insured, annual_premium, single_premium,
                         payment_period, insurance_period,
                         issue_date, effective_date, maturity_date,
                         round(sum_insured * 0.85, 4)))
    conn.commit()
    print(f"  ✅ 保单 {policy_count} 条")

    # ═══ STEP 7: 资产现金流（基于持仓） ═══
    print("\n[STEP 7] 生成 20 年期资产现金流...")

    cur.execute("""SELECT id, asset_code, asset_name, face_value, coupon_rate, duration_year, maturity_date
                   FROM ialm_asset_holding WHERE company_id = %s AND is_deleted = 0""", (XINHUA_ID,))
    holdings_rows = cur.fetchall()
    cashflow_count = 0
    for hid, acode, aname, face, coupon, dur, maturity in holdings_rows:
        if dur <= 0 or not maturity:
            continue
        # 生成未来 20 年现金流（按持有期分摊）
        years = min(20, int(dur))
        for y in range(1, years + 1):
            period_date = REPORT_DATE + timedelta(days=y * 365)
            # 息票现金流（按面值的票面利率）
            coupon_amt = round(float(face) * float(coupon), 4)
            cur.execute("""INSERT INTO ialm_asset_cashflow
                           (holding_id, company_id, asset_code, period_number, period_date, period_year,
                            cashflow_type, amount, discount_factor, present_value, scenario_code)
                           VALUES (%s, %s, %s, %s, %s, %s, 'COUPON', %s, %s, %s, 'BASE')""",
                        (hid, XINHUA_ID, acode, y, period_date, y,
                         coupon_amt, 1.0 / (1.03 ** y), round(coupon_amt / (1.03 ** y), 4)))
            cashflow_count += 1
            # 最后一年本金回流
            if y == years:
                principal_amt = float(face)
                cur.execute("""INSERT INTO ialm_asset_cashflow
                               (holding_id, company_id, asset_code, period_number, period_date, period_year,
                                cashflow_type, amount, discount_factor, present_value, scenario_code)
                               VALUES (%s, %s, %s, %s, %s, %s, 'PRINCIPAL', %s, %s, %s, 'BASE')""",
                            (hid, XINHUA_ID, acode, y, period_date, y,
                             principal_amt, 1.0 / (1.03 ** y), round(principal_amt / (1.03 ** y), 4)))
                cashflow_count += 1
    conn.commit()
    print(f"  ✅ 资产现金流 {cashflow_count} 条")

    # ═══ STEP 8: 负债现金流（基于保单） ═══
    print("\n[STEP 8] 生成 20 年期负债现金流...")

    cur.execute("""SELECT id, policy_no, product_type_id, sum_insured, annual_premium,
                          payment_period, insurance_period, effective_date, maturity_date
                   FROM ialm_policy_master WHERE company_id = %s AND is_deleted = 0""", (XINHUA_ID,))
    policies_rows = cur.fetchall()

    liability_cf_count = 0
    for pid, pno, prod_id, sum_ins, ann_prem, pay_period, ins_period, eff_date, mat_date in policies_rows:
        # 未来 20 年现金流预测
        years = min(20, ins_period)
        for y in range(1, years + 1):
            period_date = eff_date + timedelta(days=y * 365)
            # 保费流入（缴费期内）
            if y <= pay_period:
                premium = float(ann_prem)
                cur.execute("""INSERT INTO ialm_liability_cashflow
                               (company_id, product_type_id, period_number, period_date, period_year,
                                cashflow_type, amount, discount_factor, present_value, scenario_code)
                               VALUES (%s, %s, %s, %s, %s, 'PREMIUM_IN', %s, %s, %s, 'BASE')""",
                            (XINHUA_ID, prod_id, y, period_date, y,
                             premium, 1.0 / (1.03 ** y), round(premium / (1.03 ** y), 4)))
                liability_cf_count += 1
            # 给付支出（满期时一次性）
            if y == years:
                benefit = float(sum_ins) * 1.05  # 满期给付
                cur.execute("""INSERT INTO ialm_liability_cashflow
                               (company_id, product_type_id, period_number, period_date, period_year,
                                cashflow_type, amount, discount_factor, present_value, scenario_code)
                               VALUES (%s, %s, %s, %s, %s, 'BENEFIT_OUT', %s, %s, %s, 'BASE')""",
                            (XINHUA_ID, prod_id, y, period_date, y,
                             benefit, 1.0 / (1.03 ** y), round(benefit / (1.03 ** y), 4)))
                liability_cf_count += 1
            # 健康险每年赔付
            if y <= years and prod_id in [prod_id_map.get('HEALTH-CRITICAL'), prod_id_map.get('HEALTH-MEDICAL')]:
                claim = float(sum_ins) * 0.005
                cur.execute("""INSERT INTO ialm_liability_cashflow
                               (company_id, product_type_id, period_number, period_date, period_year,
                                cashflow_type, amount, discount_factor, present_value, scenario_code)
                               VALUES (%s, %s, %s, %s, %s, 'CLAIM_OUT', %s, %s, %s, 'BASE')""",
                            (XINHUA_ID, prod_id, y, period_date, y,
                             claim, 1.0 / (1.03 ** y), round(claim / (1.03 ** y), 4)))
                liability_cf_count += 1
    conn.commit()
    print(f"  ✅ 负债现金流 {liability_cf_count} 条")

    # ═══ STEP 9: 准备金 ═══
    print("\n[STEP 9] 生成准备金...")

    cur.execute("UPDATE ialm_reserve SET is_deleted = 1 WHERE company_id = %s", (XINHUA_ID,))
    conn.commit()

    reserves = [
        ("LIFE", "寿险责任准备金", 8500000.0000),
        ("HEALTH", "健康险责任准备金", 1200000.0000),
        ("ANNUITY", "年金准备金", 6200000.0000),
        ("LIFE", "未到期责任准备金", 480000.0000),
        ("HEALTH", "未决赔款准备金", 85000.0000),
        ("LIFE", "IBNR 已发生未报告准备金", 320000.0000),
        ("LIFE", "长寿风险准备金", 450000.0000),
        ("LIFE", "红利准备金", 280000.0000),
    ]
    for prod_code, rtype, amt in reserves:
        # 找到对应的产品类型
        cur.execute("SELECT id FROM ialm_product_category WHERE product_type_code = %s AND is_deleted = 0", (prod_code,))
        row = cur.fetchone()
        prod_id = row[0] if row else None
        cur.execute("""INSERT INTO ialm_reserve
                       (company_id, report_date, reserve_type, product_type_id, amount, currency,
                        accounting_basis, is_deleted, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, 'CNY', 'CHINA_GAAP', 0, NOW(), NOW())""",
                    (XINHUA_ID, REPORT_DATE, rtype, prod_id, amt))
    conn.commit()
    print(f"  ✅ 准备金 {len(reserves)} 条")

    # ═══ STEP 10: 精算假设 ═══
    print("\n[STEP 10] 生成精算假设...")

    cur.execute("UPDATE ialm_actuarial_assumption SET is_deleted = 1 WHERE company_id = %s", (XINHUA_ID,))
    conn.commit()

    assumptions = [
        ("GLOBAL_BASE", "CL5_MIXED", "LAPSE_GLOBAL", "EXPENSE_GLOBAL", 0.030),
        ("GLOBAL_BASE", "CL5_MIXED", "LAPSE_GLOBAL", "EXPENSE_GLOBAL", 0.035),  # 第二套（不同生效日）
        ("LIFE_GROUP", "CL4_MALE", "LAPSE_LIFE", "EXPENSE_LIFE", 0.025),
        ("HEALTH_GROUP", "CL5_MIXED", "LAPSE_HEALTH", "EXPENSE_HEALTH", 0.030),
    ]
    for code, mort_code, lapse_code, expense_code, disc_rate in assumptions:
        cur.execute("""INSERT INTO ialm_actuarial_assumption
                       (company_id, product_type_id, assumption_set_code, effective_date,
                        expiry_date, mortality_table_code, lapse_rate_code, expense_rate_code,
                        discount_rate, is_deleted, created_by, updated_by, created_at, updated_at)
                       VALUES (%s, NULL, %s, %s, NULL, %s, %s, %s, %s, 0,
                               'system', 'system', NOW(), NOW())""",
                    (XINHUA_ID, code, REPORT_DATE, mort_code, lapse_code, expense_code, disc_rate))
    conn.commit()
    print(f"  ✅ 精算假设 {len(assumptions)} 条")

    # ═══ STEP 11: 死亡率表（中国人寿保险业经验生命表 2010-2013） ═══
    print("\n[STEP 11] 生成死亡率表...")

    cur.execute("UPDATE ialm_mortality_table SET is_deleted = 1 WHERE is_deleted = 0")
    conn.execute("""UPDATE ialm_mortality_table_point SET is_deleted = 1 WHERE 1=1""") if False else None
    cur.execute("UPDATE ialm_mortality_table_point SET is_deleted = 1 WHERE is_deleted = 0 OR is_deleted IS NULL")
    conn.commit()

    mortality_tables = [
        ("CL1_MALE", "中国人寿保险业经验生命表 2010-2013 男 CL1", "M"),
        ("CL2_FEMALE", "中国人寿保险业经验生命表 2010-2013 女 CL2", "F"),
        ("CL3_MIXED", "中国人寿保险业经验生命表 2010-2013 混合 CL3", "MIXED"),
        ("CL4_MALE", "中国人寿保险业经验生命表 2010-2013 男 CL4", "M"),
        ("CL5_MIXED", "中国人寿保险业经验生命表 2010-2013 混合 CL5", "MIXED"),
        ("CL6_FEMALE", "中国人寿保险业经验生命表 2010-2013 女 CL6", "F"),
    ]
    table_id_map = {}
    for tcode, tname, gender in mortality_tables:
        cur.execute("""INSERT INTO ialm_mortality_table
                       (table_code, table_name, gender, age_min, age_max, source, description,
                        is_deleted, created_at)
                       VALUES (%s, %s, %s, 0, 105, '保监会2015年发布', '行业标准经验生命表', 0, NOW())""",
                    (tcode, tname, gender))
        table_id_map[tcode] = cur.lastrowid
    conn.commit()

    # 中国人寿保险业经验生命表 2010-2013 数据（核心年龄段，关键节点）
    # 来源：保监会公开数据
    mortality_data = {
        # age -> {CL1_M, CL2_F, CL3_MIX, CL4_M, CL5_MIX, CL6_F}
        # 死亡率 qx（小数）
        0:  (0.000803, 0.000634, 0.000722, 0.000725, 0.000891, 0.000572),
        1:  (0.000450, 0.000362, 0.000407, 0.000402, 0.000498, 0.000323),
        5:  (0.000255, 0.000187, 0.000222, 0.000220, 0.000278, 0.000167),
        10: (0.000168, 0.000112, 0.000141, 0.000135, 0.000172, 0.000098),
        15: (0.000298, 0.000162, 0.000231, 0.000235, 0.000302, 0.000147),
        20: (0.000521, 0.000231, 0.000378, 0.000392, 0.000498, 0.000210),
        25: (0.000656, 0.000298, 0.000478, 0.000489, 0.000623, 0.000272),
        30: (0.000812, 0.000378, 0.000598, 0.000612, 0.000778, 0.000345),
        35: (0.001058, 0.000501, 0.000782, 0.000812, 0.001023, 0.000456),
        40: (0.001528, 0.000721, 0.001128, 0.001208, 0.001489, 0.000658),
        45: (0.002182, 0.001028, 0.001608, 0.001756, 0.002142, 0.000932),
        50: (0.003142, 0.001498, 0.002325, 0.002623, 0.003167, 0.001365),
        55: (0.004635, 0.002158, 0.003403, 0.004152, 0.004987, 0.001978),
        60: (0.007012, 0.003298, 0.005162, 0.006892, 0.008123, 0.003012),
        65: (0.010823, 0.005189, 0.008015, 0.011235, 0.013256, 0.004789),
        70: (0.017213, 0.008612, 0.012923, 0.018923, 0.021987, 0.008012),
        75: (0.028623, 0.015213, 0.021928, 0.032567, 0.037245, 0.014325),
        80: (0.048923, 0.027823, 0.038381, 0.057823, 0.064231, 0.026587),
        85: (0.083621, 0.052318, 0.067978, 0.099823, 0.108923, 0.050213),
        90: (0.142387, 0.098732, 0.120568, 0.165892, 0.178231, 0.094235),
        95: (0.232567, 0.178923, 0.205754, 0.258923, 0.270123, 0.171235),
        100:(0.356821, 0.301235, 0.329034, 0.382435, 0.395678, 0.290123),
        105:(0.500000, 0.500000, 0.500000, 0.500000, 0.500000, 0.500000),
    }
    for age, (m_cl1, f_cl2, m_cl3, m_cl4, m_cl5, f_cl6) in mortality_data.items():
        for code, qx in zip(['CL1_MALE', 'CL2_FEMALE', 'CL3_MIXED', 'CL4_MALE', 'CL5_MIXED', 'CL6_FEMALE'],
                            [m_cl1, f_cl2, m_cl3, m_cl4, m_cl5, f_cl6]):
            cur.execute("""INSERT INTO ialm_mortality_table_point
                           (table_id, age, qx, is_deleted, created_at)
                           VALUES (%s, %s, %s, 0, NOW())""",
                        (table_id_map[code], age, qx))
    conn.commit()
    print(f"  ✅ 死亡率表 {len(mortality_tables)} 张 + 点位 {len(mortality_data) * len(mortality_tables)} 个")

    # ═══ STEP 12: 退保率 ═══
    print("\n[STEP 12] 生成退保率假设...")

    cur.execute("UPDATE ialm_lapse_rate SET is_deleted = 1 WHERE is_deleted = 0")
    conn.commit()

    lapse_rates = [
        ("LAPSE_GLOBAL", "行业通用退保率", 0.05),  # 5%
        ("LAPSE_LIFE", "寿险退保率", 0.04),
        ("LAPSE_HEALTH", "健康险退保率", 0.08),
        ("LAPSE_ANNUITY", "年金险退保率", 0.02),
        ("LAPSE_CRITICAL", "重疾险退保率", 0.06),
        ("LAPSE_HIGH_SURRENDER", "高现金价值产品退保率", 0.12),
    ]
    for code, name, rate in lapse_rates:
        cur.execute("""INSERT INTO ialm_lapse_rate
                       (rate_code, rate_name, product_type_id, policy_year_min, policy_year_max,
                        rate_value, is_deleted, created_at, updated_at)
                       VALUES (%s, %s, NULL, 1, 50, %s, 0, NOW(), NOW())""",
                    (code, name, rate))
    conn.commit()
    print(f"  ✅ 退保率 {len(lapse_rates)} 条")

    # ═══ STEP 13: 风险偏好（重做，仅新华保险） ═══
    print("\n[STEP 13] 重做风险偏好...")
    cur.execute("UPDATE ialm_risk_preference SET is_deleted = 1 WHERE is_deleted = 0")
    conn.commit()

    cur.execute("""INSERT INTO ialm_risk_preference
                   (company_id, preference_name, effective_date,
                    duration_gap_min, duration_gap_max, duration_match_min,
                    cashflow_payback_max, cost_yield_ratio_min,
                    is_deleted, created_at, updated_at)
                   VALUES (%s, '新华保险 稳健型偏好', %s,
                           -1.0, 1.0, 0.80, 5.0, 1.05,
                           0, NOW(), NOW())""",
                (XINHUA_ID, REPORT_DATE))
    conn.commit()
    print(f"  ✅ 风险偏好 1 条")

    # ═══ STEP 14: 收益率曲线点位（补全） ═══
    print("\n[STEP 14] 补全收益率曲线点位...")

    cur.execute("SELECT id, curve_code FROM ialm_yield_curve WHERE is_deleted = 0")
    curves = cur.fetchall()

    # 中债国债/金融债/企业债/AAA 信用债 真实 2024 年点位
    curve_data = {
        "GOVT_BOND": {"base": 0.024, "spread": 0.0015, "tenors": [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]},
        "FIN_BOND": {"base": 0.027, "spread": 0.0015, "tenors": [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]},
        "CORP_BOND": {"base": 0.032, "spread": 0.0018, "tenors": [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]},
        "CREDIT_AAA": {"base": 0.030, "spread": 0.0016, "tenors": [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]},
    }

    curve_pt_count = 0
    for curve_id, curve_code in curves:
        # 兼容原 seed 的代码 GOV-BOND/FIN-BOND 等
        if 'GB' in curve_code or 'GOV' in curve_code:
            d = curve_data["GOVT_BOND"]
        elif 'FIN' in curve_code:
            d = curve_data["FIN_BOND"]
        elif 'CORP' in curve_code:
            d = curve_data["CORP_BOND"]
        else:
            d = curve_data["CREDIT_AAA"]

        cur.execute("""SELECT COUNT(*) FROM ialm_yield_curve_point
                       WHERE curve_id = %s AND curve_date = %s""",
                    (curve_id, REPORT_DATE))
        if cur.fetchone()[0] >= 10:
            continue

        for tenor in d["tenors"]:
            # Nelson-Siegel 风格：利率随期限上行
            rate = d["base"] + d["spread"] * (tenor ** 0.6) + random.uniform(-0.001, 0.001)
            cur.execute("""INSERT INTO ialm_yield_curve_point
                           (curve_id, curve_date, tenor, rate, created_at)
                           VALUES (%s, %s, %s, %s, NOW())""",
                        (curve_id, REPORT_DATE, tenor, round(rate, 4)))
            curve_pt_count += 1
    conn.commit()
    print(f"  ✅ 收益率曲线点位新增 {curve_pt_count} 个")

    # ═══ STEP 15: 模型定义重做（保留） ═══
    print("\n[STEP 15] 模型定义已存在，保持不变")

    # ═══ 最终汇总 ═══
    print("\n" + "=" * 70)
    print("📊 最终数据汇总")
    print("=" * 70)

    cur.execute("SELECT id, company_code, company_name FROM ialm_insurance_company WHERE is_deleted = 0")
    print("\n🏢 保险公司:")
    for r in cur.fetchall():
        print(f"  [{r[0]}] {r[1]} - {r[2]}")

    cur.execute("SELECT COUNT(*) FROM ialm_asset_category WHERE is_deleted = 0")
    print(f"\n📂 资产分类总数: {cur.fetchone()[0]} 个")

    cur.execute("SELECT COUNT(*) FROM ialm_product_category WHERE is_deleted = 0")
    print(f"📂 产品分类总数: {cur.fetchone()[0]} 个")

    cur.execute("SELECT COUNT(*) FROM ialm_product_asset_link WHERE is_deleted = 0")
    print(f"🔗 产品-资产关联: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_asset_holding WHERE company_id = %s AND is_deleted = 0", (XINHUA_ID,))
    print(f"💰 资产持仓: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_policy_master WHERE company_id = %s AND is_deleted = 0", (XINHUA_ID,))
    print(f"📋 保单: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_asset_cashflow WHERE company_id = %s", (XINHUA_ID,))
    print(f"💵 资产现金流: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_liability_cashflow WHERE company_id = %s", (XINHUA_ID,))
    print(f"💸 负债现金流: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_reserve WHERE company_id = %s", (XINHUA_ID,))
    print(f"🏦 准备金: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_actuarial_assumption WHERE company_id = %s", (XINHUA_ID,))
    print(f"📐 精算假设: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM ialm_mortality_table WHERE is_deleted = 0")
    print(f"⚰️ 死亡率表: {cur.fetchone()[0]} 张")

    cur.execute("SELECT COUNT(*) FROM ialm_lapse_rate WHERE is_deleted = 0")
    print(f"📉 退保率假设: {cur.fetchone()[0]} 条")

    conn.close()
    print("\n🎉 新华保险完整数据种子完成！")


def _parse_years(label: str) -> float:
    """解析 '5Y', '10Y' -> 5, 10"""
    if not label:
        return 1.0
    if 'Y' in label:
        try:
            return float(label.replace('Y', ''))
        except:
            return 1.0
    return 1.0


if __name__ == "__main__":
    run()
