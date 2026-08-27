"""
为 风险与监管 模块生成完整 seed 数据
- ialm_risk_preference：1 条（新华保险）
- ialm_risk_indicator：8 指标 × 8 季度 = 64 条
- ialm_risk_event：18 条
- ialm_regulatory_report：4 报告类型 × 4 季度 = 16 条
- ialm_model_version：14 个模型各 1-2 个版本
- ialm_model_parameter：每个版本 3-5 个参数
"""
import pymysql
import random
import json
from datetime import date, datetime, timedelta

DB_CONFIG = dict(
    host='127.0.0.1', port=3306, user='ialm', password='Ialm@2026',
    database='ialm_db', charset='utf8mb4', autocommit=False,
)

COMPANY_ID = 4  # 新华保险

# 8 个核心风险指标（偿二代 + 5号规则）
RISK_INDICATORS = [
    # (code, name, green_min, yellow_min, red_min, current_base, unit, lower_better)
    ('SCR_RATIO',           '综合偿付能力充足率',  150,   120,  100,   185.0, '%', False),
    ('CORE_SCR_RATIO',      '核心偿付能力充足率',   75,    60,   50,    82.0, '%', False),
    ('DURATION_GAP',        '资产负债久期缺口',     -2,    -3,   -5,    -1.5, '年', True),
    ('DURATION_MATCH',      '期限结构匹配率',     0.85, 0.75, 0.65,     0.83, '比例', False),
    ('COST_YIELD_RATIO',    '综合成本收益比',     1.10, 1.05, 1.00,     1.08, '比例', False),
    ('CASHFLOW_PAYBACK',    '现金流回正期',        4.0,  5.0,  6.0,     4.5, '年', True),
    ('LCR',                 '流动性覆盖率',      1.20, 1.00, 0.80,     1.15, '比例', False),
    ('INVESTMENT_YIELD',    '综合投资收益率',     0.045, 0.035, 0.025, 0.048, '比例', False),
]

PERIODS = [
    date(2022, 3, 31), date(2022, 6, 30), date(2022, 9, 30), date(2022, 12, 31),
    date(2023, 3, 31), date(2023, 6, 30), date(2023, 9, 30), date(2023, 12, 31),
]

# 风险事件（按类型分组）
RISK_EVENTS = [
    # (code, name, type, level, trigger, threshold, days_ago, status, description)
    ('EVT-2023-001', '利率大幅上行 50bp',     'MARKET',   'HIGH',   3.95,  3.50,  90, 'RESOLVED', '2023年9月央行收紧货币政策，10年期国债收益率单周上行30bp'),
    ('EVT-2023-002', '权益市场大幅波动',      'MARKET',   'MEDIUM', -8.5, -10.0, 120, 'RESOLVED', 'A股市场单月下跌8.5%，权益类资产估值压力上升'),
    ('EVT-2023-003', '信用风险事件',         'CREDIT',   'HIGH',   1.20,  1.00,  60, 'MONITORING', '某地产企业信用债违约，影响相关持仓估值'),
    ('EVT-2023-004', '退保率上升',           'LAPSE',    'MEDIUM', 0.085, 0.060,  45, 'MONITORING', '部分分红险产品退保率上升至8.5%，超过阈值6%'),
    ('EVT-2023-005', '流动性比率短期承压',     'LIQUIDITY','MEDIUM', 1.05,  1.00,  30, 'RESOLVED', '月末大额给付导致流动性覆盖率短期低于110%'),
    ('EVT-2023-006', '偿付能力充足率下降',    'SOLVENCY', 'HIGH',   165,   150,   15, 'MONITORING', '2023Q4偿付能力充足率降至165%，需关注分红策略'),
    ('EVT-2024-001', '资产负债久期缺口扩大',  'ALM',      'MEDIUM', -3.2,  -3.0,   7, 'OPEN',       '资产端久期缩短导致缺口扩大至-3.2年'),
    ('EVT-2024-002', '重大理赔案件',         'INSURANCE','HIGH',   12000, 8000,   5, 'RESOLVED', '台风灾害导致单笔理赔1.2亿元'),
    ('EVT-2024-003', '汇率波动',            'FX',        'LOW',    7.15,  7.30,  20, 'RESOLVED', 'USD/CNY汇率波动至7.15，对外币资产影响较小'),
    ('EVT-2024-004', '监管政策变化',         'REGULATORY','LOW',    0,     0,     90, 'RESOLVED', '银保监会发布偿二代二期新规'),
    ('EVT-2024-005', '操作风险事件',         'OPERATIONAL','MEDIUM', 0,    0,    180, 'RESOLVED', '某业务系统故障导致数据延迟上报'),
    ('EVT-2024-006', '战略资产配置偏离',      'STRATEGIC','MEDIUM', 0.08, 0.05,  10, 'OPEN',       '权益类资产配置比例偏离战略目标8%'),
    ('EVT-2024-007', '流动性覆盖率预警',      'LIQUIDITY','HIGH',   1.00,  1.20,   3, 'MONITORING', '流动性覆盖率降至100%，低于120%预警阈值'),
    ('EVT-2024-008', '投资收益率下滑',       'INVESTMENT','LOW',   0.038, 0.045, 25, 'RESOLVED', '综合投资收益率降至3.8%'),
    ('EVT-2024-009', '重大关联交易',         'COMPLIANCE','LOW',    0,     0,    150, 'RESOLVED', '披露2023年关联方交易信息'),
    ('EVT-2024-010', '声誉风险',            'REPUTATION','LOW',    0,     0,     35, 'RESOLVED', '客户投诉事件，已妥善处理'),
    ('EVT-2024-011', '死亡率恶化',           'MORTALITY', 'MEDIUM', 0.0075, 0.0060, 60, 'MONITORING', '经验死亡率较预期恶化12%'),
    ('EVT-2024-012', '监管现场检查发现',      'REGULATORY','MEDIUM', 0,     0,    100, 'MONITORING', '监管现场检查发现3项需整改问题'),
]

# 监管报表（4 报告类型）
REG_REPORTS = [
    # (report_type, report_period, report_date, filing_deadline, file_path, status)
    ('偿付能力季报',      '2023Q1', date(2023, 4, 30),  date(2023, 5, 15),  '/reports/2023Q1_solvency.xlsx',  'FILED'),
    ('偿付能力季报',      '2023Q2', date(2023, 7, 31),  date(2023, 8, 15),  '/reports/2023Q2_solvency.xlsx',  'FILED'),
    ('偿付能力季报',      '2023Q3', date(2023, 10, 31), date(2023, 11, 15), '/reports/2023Q3_solvency.xlsx',  'FILED'),
    ('偿付能力季报',      '2023Q4', date(2024, 1, 31),  date(2024, 2, 15),  '/reports/2023Q4_solvency.xlsx',  'FILED'),
    ('偿付能力季报',      '2024Q1', date(2024, 4, 30),  date(2024, 5, 15),  '/reports/2024Q1_solvency.xlsx',  'DRAFT'),
    ('资产负债季报',      '2023Q1', date(2023, 4, 30),  date(2023, 5, 20),  '/reports/2023Q1_alm.xlsx',      'FILED'),
    ('资产负债季报',      '2023Q2', date(2023, 7, 31),  date(2023, 8, 20),  '/reports/2023Q2_alm.xlsx',      'FILED'),
    ('资产负债季报',      '2023Q3', date(2023, 10, 31), date(2023, 11, 20), '/reports/2023Q3_alm.xlsx',      'FILED'),
    ('资产负债季报',      '2023Q4', date(2024, 1, 31),  date(2024, 2, 20),  '/reports/2023Q4_alm.xlsx',      'FILED'),
    ('资产负债季报',      '2024Q1', date(2024, 4, 30),  date(2024, 5, 20),  '/reports/2024Q1_alm.xlsx',      'DRAFT'),
    ('风险综合评级季度报告', '2023Q1', date(2023, 4, 30), date(2023, 5, 30), '/reports/2023Q1_irr.xlsx',         'FILED'),
    ('风险综合评级季度报告', '2023Q2', date(2023, 7, 31), date(2023, 8, 30), '/reports/2023Q2_irr.xlsx',         'FILED'),
    ('风险综合评级季度报告', '2023Q3', date(2023, 10, 31),date(2023, 11, 30),'/reports/2023Q3_irr.xlsx',         'FILED'),
    ('风险综合评级季度报告', '2023Q4', date(2024, 1, 31), date(2024, 2, 28), '/reports/2023Q4_irr.xlsx',         'FILED'),
    ('风险综合评级季度报告', '2024Q1', date(2024, 4, 30), date(2024, 5, 30), '/reports/2024Q1_irr.xlsx',         'DRAFT'),
    ('重大事项报告',      '2023-09', date(2023, 9, 15), date(2023, 9, 18), '/reports/2023-09_event.docx',   'FILED'),
]


def calc_alert_level(value, green, yellow, red, lower_better):
    """计算预警等级"""
    if lower_better:
        if value <= green:
            return 'GREEN', 'STABLE'
        elif value <= yellow:
            return 'YELLOW', 'UP' if value < 0 else 'STABLE'
        else:
            return 'RED', 'UP'
    else:
        if value >= green:
            return 'GREEN', 'STABLE'
        elif value >= yellow:
            return 'YELLOW', 'DOWN'
        else:
            return 'RED', 'DOWN'


def main():
    conn = pymysql.connect(**DB_CONFIG)
    today = date(2024, 5, 1)
    with conn.cursor() as c:
        # 清空旧数据
        for tbl in ['ialm_risk_preference', 'ialm_risk_indicator', 'ialm_risk_event',
                    'ialm_regulatory_report', 'ialm_model_version', 'ialm_model_parameter']:
            c.execute(f"DELETE FROM {tbl}")
        conn.commit()
        print("Cleared old risk/regulatory data")

        # ── 1. 风险偏好 ──
        c.execute("""INSERT INTO ialm_risk_preference
            (company_id, preference_name, effective_date, expiry_date,
             duration_gap_min, duration_gap_max, duration_match_min,
             cashflow_payback_max, cost_yield_ratio_min, extra_json, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)""",
            (COMPANY_ID, '2024年度风险偏好陈述书', date(2024, 1, 1), date(2024, 12, 31),
             -2.0, 2.0, 0.85, 5.0, 1.10,
             json.dumps({
                 "approved_by": "董事会",
                 "approval_date": "2023-12-25",
                 "solvency_target": {"comprehensive": 150, "core": 75},
                 "investment_risk_budget": 0.08,
                 "liquidity_target": 1.20,
             }, ensure_ascii=False)))
        conn.commit()
        print("Inserted 1 risk preference")

        # ── 2. 风险指标（8 指标 × 8 季度 = 64） ──
        random.seed(42)
        ind_count = 0
        for code, name, green, yellow, red, base, unit, lower_better in RISK_INDICATORS:
            for i, period in enumerate(PERIODS):
                # 模拟指标值的合理波动
                if code == 'SCR_RATIO':
                    val = base - i * 5 + random.uniform(-5, 5)
                elif code == 'DURATION_GAP':
                    val = base - i * 0.3 + random.uniform(-0.3, 0.3)
                elif code == 'CASHFLOW_PAYBACK':
                    val = base + i * 0.1 + random.uniform(-0.2, 0.2)
                elif code == 'INVESTMENT_YIELD':
                    val = base - i * 0.001 + random.uniform(-0.002, 0.002)
                else:
                    val = base + random.uniform(-0.02, 0.02) * (green - red)

                val = round(val, 4)
                alert, trend = calc_alert_level(val, green, yellow, red, lower_better)
                c.execute("""INSERT INTO ialm_risk_indicator
                    (company_id, indicator_code, indicator_name, report_date,
                     current_value, threshold_green, threshold_yellow, threshold_red,
                     alert_level, trend, extra_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (COMPANY_ID, code, name, period,
                     val, green, yellow, red,
                     alert, trend,
                     json.dumps({"unit": unit, "lower_better": lower_better,
                                 "computation": f"基于 {code} 标准计算"}, ensure_ascii=False)))
                ind_count += 1
        conn.commit()
        print(f"Inserted {ind_count} risk indicators")

        # ── 3. 风险事件（18 条） ──
        evt_count = 0
        for code, name, etype, level, trigger, threshold, days_ago, status, desc in RISK_EVENTS:
            occurred = datetime(2024, 5, 1) - timedelta(days=days_ago)
            resolved = occurred + timedelta(days=random.randint(3, 30)) if status == 'RESOLVED' else None
            resolved_by = 1 if status == 'RESOLVED' else None
            resolution = (f"已通过 {'风险缓释措施' if level == 'HIGH' else '内部调整'} 处置完毕"
                          if status == 'RESOLVED' else None)
            c.execute("""INSERT INTO ialm_risk_event
                (company_id, event_code, event_name, event_level, event_type,
                 trigger_value, threshold_value, trigger_date, status,
                 description, resolution, resolved_at, resolved_by, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)""",
                (COMPANY_ID, code, name, level, etype,
                 trigger, threshold, occurred, status,
                 desc, resolution, resolved, resolved_by))
            evt_count += 1
        conn.commit()
        print(f"Inserted {evt_count} risk events")

        # ── 4. 监管报表（16 条） ──
        reg_count = 0
        for rtype, period, rdate, deadline, fpath, status in REG_REPORTS:
            filed = rdate + timedelta(days=random.randint(3, 12)) if status == 'FILED' else None
            detail = {
                "submission_channel": "银保监会 EAST 系统",
                "responsible_person": "财务部 / 风险管理部",
                "checksum": f"sha256:{random.randint(100000, 999999):06x}",
                "file_size_kb": random.randint(200, 5000),
            }
            c.execute("""INSERT INTO ialm_regulatory_report
                (company_id, report_type, report_period, report_date,
                 filing_deadline, file_path, file_format, status,
                 filed_at, detail_json, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)""",
                (COMPANY_ID, rtype, period, rdate,
                 deadline, fpath, 'EXCEL' if fpath.endswith('.xlsx') else 'DOCX',
                 status, filed, json.dumps(detail, ensure_ascii=False)))
            reg_count += 1
        conn.commit()
        print(f"Inserted {reg_count} regulatory reports")

        # ── 5. 模型版本 + 参数 ──
        # 获取现有模型
        c.execute("SELECT id, model_code, model_name, category FROM ialm_model_definition WHERE is_deleted = 0 ORDER BY id")
        models = c.fetchall()
        ver_count = 0
        par_count = 0
        for mid, mcode, mname, mcat in models:
            # 每个模型 1-2 个版本
            v1_date = date(2023, 6, 30)
            v1_code = 'v1.0.0'
            c.execute("""INSERT INTO ialm_model_version
                (model_id, version_code, version_name, changelog, release_date,
                 is_current, parameters_json, benchmark_metrics_json, is_deleted)
                VALUES (%s, %s, %s, %s, %s, 0, %s, %s, 0)""",
                (mid, v1_code, f"{mname} 初始版本", f"首版发布：实现 {mcode} 基础算法",
                 v1_date,
                 json.dumps({"initial_release": True, "test_dataset": "2022Q1-2023Q1"}),
                 json.dumps({"accuracy": round(random.uniform(0.85, 0.95), 4),
                             "rmse": round(random.uniform(0.02, 0.08), 4),
                             "stability_score": round(random.uniform(0.7, 0.9), 4)})))
            ver_count += 1
            v1_id = c.lastrowid

            # v1 的参数（3-4 个）
            base_params = [
                ('RISK_FREE_RATE', '无风险利率', '0.0250', 'DECIMAL', '0.0250', '10年期国债收益率'),
                ('CONFIDENCE_LEVEL', '置信水平', '0.9950', 'DECIMAL', '0.9500', '偿二代标准'),
                ('LOOKBACK_PERIOD', '回看期', '252', 'INT', '252', '1年交易日数'),
            ]
            if 'DURATION' in mcode or 'MATCH' in mcode:
                base_params.append(('MAX_DURATION', '最大久期', '30', 'INT', '30', '年'))
            elif 'STRESS' in mcode or 'SCENARIO' in mcode:
                base_params.append(('MAX_VAR', '最大方差', '0.04', 'DECIMAL', '0.04', 'Markowitz约束'))
            elif 'YIELD' in mcode:
                base_params.append(('CURVE_TYPE', '曲线类型', 'NELSON_SIEGEL', 'STRING', 'NELSON_SIEGEL', 'Nelson-Siegel 模型'))

            for pcode, pname, pval, ptype, dval, pdesc in base_params:
                c.execute("""INSERT INTO ialm_model_parameter
                    (model_version_id, param_code, param_name, param_value,
                     param_type, default_value, description, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 0)""",
                    (v1_id, pcode, pname, pval, ptype, dval, pdesc))
                par_count += 1

            # 50% 概率加 v1.1（小改进）
            if random.random() < 0.5:
                v2_date = date(2024, 3, 31)
                v2_code = 'v1.1.0'
                c.execute("""INSERT INTO ialm_model_version
                    (model_id, version_code, version_name, changelog, release_date,
                     is_current, parameters_json, benchmark_metrics_json, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 0)""",
                    (mid, v2_code, f"{mname} 优化版", f"性能优化：参数调优，accuracy +5%",
                     v2_date,
                     json.dumps({"optimization": "NSGA-II 多目标优化",
                                 "test_dataset": "2023Q2-2023Q4"}),
                     json.dumps({"accuracy": round(random.uniform(0.90, 0.98), 4),
                                 "rmse": round(random.uniform(0.01, 0.04), 4),
                                 "stability_score": round(random.uniform(0.8, 0.95), 4)})))
                ver_count += 1
                v2_id = c.lastrowid
                # v2 的参数（带新值）
                for pcode, pname, _, ptype, dval, pdesc in base_params:
                    new_val = dval
                    if pcode == 'CONFIDENCE_LEVEL':
                        new_val = '0.9950'  # 提升到偿二代
                    elif pcode == 'RISK_FREE_RATE':
                        new_val = '0.0275'  # 折现率更新
                    elif pcode == 'LOOKBACK_PERIOD':
                        new_val = '504'  # 扩展为 2 年
                    c.execute("""INSERT INTO ialm_model_parameter
                        (model_version_id, param_code, param_name, param_value,
                         param_type, default_value, description, is_deleted)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 0)""",
                        (v2_id, pcode, pname, new_val, ptype, dval, pdesc))
                    par_count += 1

        conn.commit()
        print(f"Inserted {ver_count} model versions, {par_count} model parameters")

    conn.close()
    print("\n=== Done ===")


if __name__ == '__main__':
    main()