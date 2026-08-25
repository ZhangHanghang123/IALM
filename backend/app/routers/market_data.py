"""IALM 市场数据 API（利率曲线/汇率/股票指数/信用利差）"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/market-data", tags=["市场数据"])


# ═══ 1. 收益率曲线 ═══
@router.get("/yield-curves")
def list_yield_curves(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """收益率曲线列表"""
    rows = db.execute(
        text("""SELECT id, curve_code, curve_name, curve_type, currency, effective_date, source
              FROM ialm_yield_curve WHERE is_deleted = 0
              ORDER BY effective_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_yield_curve WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "curve_code": r[1], "curve_name": r[2], "curve_type": r[3],
             "currency": r[4], "effective_date": r[5].isoformat() if r[5] else None, "source": r[6]}
            for r in rows
        ],
    }


@router.get("/yield-curves/{curve_id}/points")
def get_curve_points(curve_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    """收益率曲线点位数据"""
    rows = db.execute(
        text("""SELECT id, tenor_years, tenor_label, rate, is_zero, is_par, is_forward
              FROM ialm_yield_curve_point WHERE curve_id = :cid AND is_deleted = 0
              ORDER BY tenor_years"""),
        {"cid": curve_id},
    ).fetchall()
    return {
        "curve_id": curve_id,
        "points": [
            {"id": r[0], "tenor_years": float(r[1] or 0), "tenor_label": r[2],
             "rate": float(r[3] or 0), "is_zero": r[4], "is_par": r[5], "is_forward": r[6]}
            for r in rows
        ],
    }


# ═══ 2. 汇率 ═══
@router.get("/fx-rates")
def list_fx_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT id, currency_pair, rate, rate_type, effective_date, source
              FROM ialm_fx_rate WHERE is_deleted = 0
              ORDER BY effective_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_fx_rate WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "currency_pair": r[1], "rate": float(r[2] or 0),
             "rate_type": r[3], "effective_date": r[4].isoformat() if r[4] else None, "source": r[5]}
            for r in rows
        ],
    }


# ═══ 3. 股票指数 ═══
@router.get("/equity-indices")
def list_equity_indices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT id, index_code, index_name, exchange, level, change_pct, trade_date
              FROM ialm_equity_index WHERE is_deleted = 0
              ORDER BY trade_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_equity_index WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "index_code": r[1], "index_name": r[2], "exchange": r[3],
             "level": float(r[4] or 0), "change_pct": float(r[5] or 0),
             "trade_date": r[6].isoformat() if r[6] else None}
            for r in rows
        ],
    }


# ═══ 4. 信用利差 ═══
@router.get("/credit-spreads")
def list_credit_spreads(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT id, rating, sector, tenor_years, spread_bps, effective_date
              FROM ialm_credit_spread WHERE is_deleted = 0
              ORDER BY effective_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_credit_spread WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "rating": r[1], "sector": r[2], "tenor_years": float(r[3] or 0),
             "spread_bps": float(r[4] or 0), "effective_date": r[5].isoformat() if r[5] else None}
            for r in rows
        ],
    }