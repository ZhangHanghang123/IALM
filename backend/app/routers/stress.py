"""IALM 压力测试 API（监管预置情景 + 用户自定义情景 + 结果）"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
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
    return {
        "total": total,
        "items": [
            {"id": r[0], "scenario_code": r[1], "scenario_name": r[2], "scenario_type": r[3],
             "source": r[4], "description": r[5], "shocks_json": r[6], "is_active": r[7]}
            for r in rows
        ],
    }


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