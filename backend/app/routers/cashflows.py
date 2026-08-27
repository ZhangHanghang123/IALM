"""IALM 现金流测算引擎 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user
from ..services.cashflow_engine import CashflowGenerationService

router = APIRouter(prefix="/cashflows", tags=["现金流引擎"])


class RegenerateRequest(BaseModel):
    company_id: int
    scenario_code: str = 'BASE'
    curve_code: str = 'CN-GB-2025'


@router.post("/engine/regenerate")
def regenerate(
    body: RegenerateRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """全量重算某公司的资产+负债现金流"""
    service = CashflowGenerationService(db, body.curve_code)
    result = service.regenerate_all(body.company_id, body.scenario_code)
    return result


@router.get("/engine/status")
def engine_status(
    company_id: int,
    curve_code: str = Query('CN-GB-2025'),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """查看引擎状态（数据覆盖、PV 合计、收益率曲线）"""
    service = CashflowGenerationService(db, curve_code)
    return service.status(company_id)


@router.get("/engine/curves")
def list_curves(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """可用的收益率曲线"""
    rows = db.execute(
        text("""SELECT id, curve_code, curve_name, curve_type, currency, data_source
                FROM ialm_yield_curve WHERE is_deleted = 0 ORDER BY id"""),
    ).fetchall()
    pts = db.execute(
        text("""SELECT curve_id, COUNT(*) AS point_count,
                       MIN(tenor) AS min_tenor, MAX(tenor) AS max_tenor
                FROM ialm_yield_curve_point GROUP BY curve_id"""),
    ).fetchall()
    pt_map = {r[0]: (int(r[1]), float(r[2]), float(r[3])) for r in pts}
    return {
        "items": [
            {"id": r[0], "curve_code": r[1], "curve_name": r[2], "curve_type": r[3],
             "currency": r[4], "data_source": r[5],
             "point_count": pt_map.get(r[0], (0, 0, 0))[0],
             "min_tenor": pt_map.get(r[0], (0, 0, 0))[1],
             "max_tenor": pt_map.get(r[0], (0, 0, 0))[2]}
            for r in rows
        ]
    }