"""IALM 风险预警 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/risk", tags=["风险预警"])


# ═══ 1. 风险偏好（RiskPreference） ═══
@router.get("/preferences")
def list_preferences(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT id, company_id, preference_level, max_drawdown, max_var, max_duration_gap,
                     target_solvency_ratio, target_lcr, effective_date, approved_by
              FROM ialm_risk_preference WHERE is_deleted = 0
              ORDER BY company_id, effective_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_preference WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "preference_level": r[2],
             "max_drawdown": float(r[3] or 0), "max_var": float(r[4] or 0),
             "max_duration_gap": float(r[5] or 0), "target_solvency_ratio": float(r[6] or 0),
             "target_lcr": float(r[7] or 0), "effective_date": r[8].isoformat() if r[8] else None,
             "approved_by": r[9]}
            for r in rows
        ],
    }


# ═══ 2. 风险指标监控 ═══
@router.get("/indicators")
def list_risk_indicators(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT ri.id, ri.company_id, c.company_short AS company_name,
                     ri.indicator_code, ri.indicator_name, ri.current_value, ri.threshold_value,
                     ri.warning_level, ri.monitor_date, ri.status
              FROM ialm_risk_indicator ri
              LEFT JOIN ialm_insurance_company c ON c.id = ri.company_id AND c.is_deleted = 0
              WHERE ri.is_deleted = 0
              ORDER BY ri.warning_level DESC, ri.current_value DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_indicator WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "indicator_code": r[3], "indicator_name": r[4], "current_value": float(r[5] or 0),
             "threshold_value": float(r[6] or 0), "warning_level": r[7],
             "monitor_date": r[8].isoformat() if r[8] else None, "status": r[9]}
            for r in rows
        ],
    }


# ═══ 3. 风险事件 ═══
@router.get("/events")
def list_risk_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT re.id, re.company_id, c.company_short AS company_name,
                     re.event_type, re.event_level, re.title, re.description,
                     re.occurred_at, re.status, re.handler
              FROM ialm_risk_event re
              LEFT JOIN ialm_insurance_company c ON c.id = re.company_id AND c.is_deleted = 0
              WHERE re.is_deleted = 0
              ORDER BY re.occurred_at DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_event WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "event_type": r[3], "event_level": r[4], "title": r[5], "description": r[6],
             "occurred_at": r[7].isoformat() if r[7] else None,
             "status": r[8], "handler": r[9]}
            for r in rows
        ],
    }


# ═══ 4. 监管报表 ═══
@router.get("/regulatory-reports")
def list_regulatory_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT rr.id, rr.company_id, c.company_short AS company_name,
                     rr.report_type, rr.report_period, rr.submit_date,
                     rr.compliance_status, rr.remark
              FROM ialm_regulatory_report rr
              LEFT JOIN ialm_insurance_company c ON c.id = rr.company_id AND c.is_deleted = 0
              WHERE rr.is_deleted = 0
              ORDER BY rr.submit_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_regulatory_report WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "report_type": r[3], "report_period": r[4],
             "submit_date": r[5].isoformat() if r[5] else None,
             "compliance_status": r[6], "remark": r[7]}
            for r in rows
        ],
    }