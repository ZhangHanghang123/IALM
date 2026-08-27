"""IALM 压力测试 API（监管预置情景 + 用户自定义情景 + 结果）"""
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/stress", tags=["压力测试"])


# ═══ 1. 监管预置压力情景 ═══
@router.get("/scenarios")
def list_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """监管预置压力情景（6 个银保监会必选情景）"""
    rows = db.execute(
        text("""SELECT id, scenario_code, scenario_name, scenario_type, source,
                     description, shocks_json, is_active
              FROM ialm_stress_scenario WHERE is_deleted = 0
              ORDER BY source DESC, scenario_code LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_stress_scenario WHERE is_deleted = 0")).scalar() or 0
    items = []
    for r in rows:
        try:
            shocks = json.loads(r[6]) if r[6] else {"factors": []}
        except Exception:
            shocks = {"factors": []}
        items.append({
            "id": r[0], "scenario_code": r[1], "scenario_name": r[2], "scenario_type": r[3],
            "source": r[4], "description": r[5], "shocks_json": shocks, "is_active": r[7],
        })
    return {"total": total, "items": items}


# ═══ 1.1 创建自定义情景 ═══
class ScenarioCreate(BaseModel):
    scenario_code: str
    scenario_name: str
    scenario_type: str
    source: str = "CUSTOM"
    description: str = ""
    shocks_json: Dict[str, Any]


@router.post("/scenarios")
def create_scenario(
    body: ScenarioCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """创建自定义压力情景"""
    exists = db.execute(
        text("SELECT id FROM ialm_stress_scenario WHERE scenario_code = :c AND is_deleted = 0"),
        {"c": body.scenario_code},
    ).fetchone()
    if exists:
        raise HTTPException(400, detail=f"情景编码 {body.scenario_code} 已存在")
    rid = db.execute(
        text("""INSERT INTO ialm_stress_scenario
              (scenario_code, scenario_name, scenario_type, source, description,
               shocks_json, is_active, is_deleted, created_by, updated_by, created_at, updated_at)
              VALUES (:c, :n, :t, :s, :d, :j, 1, 0, :u, :u, NOW, NOW)"""),
        {
            "c": body.scenario_code,
            "n": body.scenario_name,
            "t": body.scenario_type,
            "s": body.source,
            "d": body.description,
            "j": json.dumps(body.shocks_json, ensure_ascii=False),
            "u": user.get("sub", "system"),
        },
    ).lastrowid
    db.commit()
    return {"id": rid, "scenario_code": body.scenario_code}


# ═══ 1.2 修改情景（监管 + 自定义均可） ═══
class ScenarioUpdate(BaseModel):
    scenario_name: Optional[str] = None
    scenario_type: Optional[str] = None
    description: Optional[str] = None
    shocks_json: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = None


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
        # 英文编码
        "LIFE": 12.0,
        "UNIVERSAL_LIFE": 10.0,
        "ANNUITY": 15.0,
        "HEALTH": 4.0,
        "ACCIDENT": 2.0,
        "CLAIM": 1.0,
        "UN_EARNED_PREMIUM": 1.5,
        "UN_DERIVED": 0.5,
        # 中文准备金类型（实际数据）
        "寿险责任准备金": 12.0,
        "健康险责任准备金": 4.0,
        "年金准备金": 15.0,
        "未到期责任准备金": 1.5,
        "未决赔款准备金": 1.0,
        "IBNR 已发生未报告准备金": 1.0,
        "长寿风险准备金": 14.0,
        "红利准备金": 8.0,
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


@router.put("/scenarios/{scenario_id}")
def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """修改压力情景配置（用户可在监管预置基础上调整）"""
    exists = db.execute(
        text("SELECT id, source FROM ialm_stress_scenario WHERE id = :id AND is_deleted = 0"),
        {"id": scenario_id},
    ).fetchone()
    if not exists:
        raise HTTPException(404, detail="情景不存在")

    updates = []
    params: Dict[str, Any] = {"id": scenario_id, "u": user.get("sub", "system")}
    if body.scenario_name is not None:
        updates.append("scenario_name = :n"); params["n"] = body.scenario_name
    if body.scenario_type is not None:
        updates.append("scenario_type = :t"); params["t"] = body.scenario_type
    if body.description is not None:
        updates.append("description = :d"); params["d"] = body.description
    if body.shocks_json is not None:
        updates.append("shocks_json = :j"); params["j"] = json.dumps(body.shocks_json, ensure_ascii=False)
    if body.is_active is not None:
        updates.append("is_active = :a"); params["a"] = body.is_active

    if not updates:
        return {"updated": 0, "id": scenario_id}

    updates.append("updated_by = :u")
    updates.append("updated_at = NOW()")
    sql = f"UPDATE ialm_stress_scenario SET {', '.join(updates)} WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    return {"updated": 1, "id": scenario_id}


# ═══ 1.3 软删除情景 ═══
@router.delete("/scenarios/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = db.execute(
        text("SELECT source FROM ialm_stress_scenario WHERE id = :id AND is_deleted = 0"),
        {"id": scenario_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, detail="情景不存在")
    if row[0] == "REG":
        raise HTTPException(400, detail="监管预置情景不允许删除（可修改或停用）")
    db.execute(
        text("UPDATE ialm_stress_scenario SET is_deleted = 1, updated_by = :u, updated_at = NOW() WHERE id = :id"),
        {"u": user.get("sub", "system"), "id": scenario_id},
    )
    db.commit()
    return {"deleted": True, "id": scenario_id}


# ═══ 2. 压力测试结果 ═══
@router.get("/results")
def list_stress_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT sr.id, sr.company_id, c.company_short AS company_name,
                     sr.scenario_id, s.scenario_name,
                     sr.test_date, sr.nav_impact, sr.scr_change, sr.lcr_change, sr.passed
              FROM ialm_stress_result sr
              LEFT JOIN ialm_insurance_company c ON c.id = sr.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_stress_scenario s ON s.id = sr.scenario_id AND s.is_deleted = 0
              WHERE sr.is_deleted = 0
              ORDER BY sr.test_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_stress_result WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2], "scenario_id": r[3],
             "scenario_name": r[4], "test_date": r[5].isoformat() if r[5] else None,
             "nav_impact": float(r[6] or 0), "scr_change": float(r[7] or 0),
             "lcr_change": float(r[8] or 0), "passed": r[9]}
            for r in rows
        ],
    }


# ═══ 3. 简单压力测试模拟器（运行 ALG-007 多因子冲击） ═══
class StressRunRequest(BaseModel):
    company_id: int
    scenario_id: int
    asset_value: float
    liability_value: float
    asset_duration: float
    liability_duration: float
    base_scr: float


@router.post("/run")
def run_stress_simulation(
    body: StressRunRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    运行压力测试（简化版：基于久期缺口的多因子冲击传导）
    ΔNAV = -(D_A·A - D_L·L)·Δy + 0.5·(C_A·A - C_L·L)·(Δy)²
    """
    import json

    # 读取情景冲击
    row = db.execute(
        text("SELECT scenario_code, scenario_name, shocks_json FROM ialm_stress_scenario WHERE id = :id AND is_deleted = 0"),
        {"id": body.scenario_id},
    ).fetchone()
    if not row:
        return {"error": "情景不存在"}
    shocks = json.loads(row[2]) if row[2] else {}
    factors = shocks.get("factors", [])

    A = body.asset_value
    L = body.liability_value
    D_A = body.asset_duration
    D_L = body.liability_duration

    # 默认凸性 65 / 72（5号规则缺省值）
    C_A, C_L = 65, 72

    nav_change = 0.0
    detail = []
    for f in factors:
        name = f.get("name", "")
        ftype = f.get("type", "")
        value = f.get("value", 0)
        if ftype == "parallel_shift":
            # 利率冲击 Δy (decimals)
            delta_y = value / 100.0
            impact = -(D_A * A - D_L * L) * delta_y + 0.5 * (C_A * A - C_L * L) * (delta_y ** 2)
            nav_change += impact
            detail.append({"factor": name, "value": value, "impact": round(impact, 2), "unit": "bp"})
        elif ftype == "multiplier":
            if name == "investment_yield":
                impact = A * (value - 1)  # 投资收益率下降
                nav_change += impact
                detail.append({"factor": name, "value": value, "impact": round(impact, 2), "unit": "ratio"})
            elif name == "lapse_rate":
                impact = L * (value - 1) * 0.05  # 退保冲击（简化）
                nav_change += impact
                detail.append({"factor": name, "value": value, "impact": round(impact, 2), "unit": "ratio"})

    new_nav = A - L + nav_change
    scr_change_pct = (nav_change / body.base_scr) * 100 if body.base_scr else 0
    passed = abs(scr_change_pct) < 100  # SCR变化 < 100% 为通过

    return {
        "scenario_code": row[0],
        "scenario_name": row[1],
        "company_id": body.company_id,
        "base_asset_value": A,
        "base_liability_value": L,
        "base_net_value": round(A - L, 2),
        "nav_change": round(nav_change, 2),
        "new_net_value": round(new_nav, 2),
        "scr_change_pct": round(scr_change_pct, 4),
        "passed": passed,
        "detail": detail,
    }