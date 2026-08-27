"""Insert base-parameters endpoint after ScenarioUpdate class."""
import re

path = r"C:\银行经营\IALM\backend\app\routers\stress.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoint = '''

# ═══ 1.3 从基础数据统计压力测试参数 ═══
@router.get("/base-parameters")
def base_parameters(
    company_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    从系统基础数据自动聚合运行参数：
    - 资产规模 = SUM(cost_value) from ialm_asset_holding
    - 负债规模 = SUM(amount) from ialm_reserve
    - 资产久期 = SUM(cost_value * duration_year) / SUM(cost_value) 加权平均
    - 负债久期 = 按准备金类型加权估算
    - 基础 SCR = 负债规模 × 12%（偿二代最低偿付能力比率）
    """
    asset_row = db.execute(
        text("""SELECT
                  COALESCE(SUM(cost_value), 0)               AS total_cost,
                  COALESCE(SUM(market_value), 0)             AS total_market,
                  COALESCE(SUM(cost_value * duration_year) / NULLIF(SUM(cost_value), 0), 0) AS weighted_dur,
                  COUNT(*)                                    AS holding_count
                FROM ialm_asset_holding
                WHERE company_id = :cid AND is_deleted = 0"""),
        {"cid": company_id},
    ).fetchone()
    asset_value = float(asset_row[0] or 0)
    asset_market_value = float(asset_row[1] or 0)
    asset_duration = float(asset_row[2] or 0)
    asset_count = int(asset_row[3] or 0)

    liab_rows = db.execute(
        text("""SELECT reserve_type,
                       COALESCE(SUM(amount), 0) AS amt,
                       COUNT(*) AS cnt
                FROM ialm_reserve
                WHERE company_id = :cid AND is_deleted = 0
                GROUP BY reserve_type"""),
        {"cid": company_id},
    ).fetchall()

    liability_value = sum(float(r[1] or 0) for r in liab_rows)

    duration_by_type = {
        "LIFE": 12.0,
        "UNIVERSAL_LIFE": 10.0,
        "ANNUITY": 15.0,
        "HEALTH": 4.0,
        "ACCIDENT": 2.0,
        "CLAIM": 1.0,
        "UN_EARNED_PREMIUM": 1.5,
        "UN_DERIVED": 0.5,
    }
    weighted_liab_dur = 0.0
    for r in liab_rows:
        rtype = r[0] or ""
        amt = float(r[1] or 0)
        dur = duration_by_type.get(rtype, 6.0)
        weighted_liab_dur += amt * dur
    liability_duration = weighted_liab_dur / liability_value if liability_value else 0.0

    scr_row = db.execute(
        text("""SELECT COALESCE(AVG(discount_rate), 0) FROM ialm_actuarial_assumption
                WHERE company_id = :cid AND is_deleted = 0
                  AND assumption_set_code LIKE '%BASE%'"""),
        {"cid": company_id},
    ).fetchone()
    discount_rate = float(scr_row[0] or 0)
    target_scr_ratio = 0.12
    base_scr = liability_value * target_scr_ratio

    co_row = db.execute(
        text("SELECT company_short FROM ialm_insurance_company WHERE id = :cid AND is_deleted = 0"),
        {"cid": company_id},
    ).fetchone()
    company_short = co_row[0] if co_row else f"公司#{company_id}"

    return {
        "company_id": company_id,
        "company_short": company_short,
        "asset_value": round(asset_value, 2),
        "asset_market_value": round(asset_market_value, 2),
        "liability_value": round(liability_value, 2),
        "asset_duration": round(asset_duration, 4),
        "liability_duration": round(liability_duration, 4),
        "base_scr": round(base_scr, 2),
        "discount_rate": round(discount_rate, 4),
        "summary": {
            "asset_holding_count": asset_count,
            "liability_reserve_total": round(liability_value, 2),
            "reserve_by_type": [
                {"type": r[0], "amount": float(r[1] or 0), "count": int(r[2] or 0)}
                for r in liab_rows
            ],
            "scr_ratio_used": target_scr_ratio,
        },
    }
'''

# Find the location after ScenarioUpdate class but before @router.put
pattern = r'(class ScenarioUpdate\(BaseModel\):[\s\S]*?is_active: Optional\[int\] = None\n)'
if re.search(pattern, content):
    new_content = re.sub(pattern, r'\1' + new_endpoint, content, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("OK: endpoint inserted")
else:
    print("ERR: pattern not found")