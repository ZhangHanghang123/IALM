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
        text("""SELECT id, curve_code, curve_name, curve_type, currency, data_source, created_at
              FROM ialm_yield_curve WHERE is_deleted = 0
              ORDER BY curve_code LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_yield_curve WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "curve_code": r[1], "curve_name": r[2], "curve_type": r[3],
             "currency": r[4], "data_source": r[5],
             "created_at": r[6].isoformat() if r[6] else None}
            for r in rows
        ],
    }


@router.get("/yield-curves/{curve_id}/points")
def get_curve_points(curve_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    """收益率曲线点位数据"""
    rows = db.execute(
        text("""SELECT id, curve_id, curve_date, tenor, rate
              FROM ialm_yield_curve_point WHERE curve_id = :cid
              ORDER BY tenor"""),
        {"cid": curve_id},
    ).fetchall()
    return {
        "curve_id": curve_id,
        "total": len(rows),
        "points": [
            {"id": r[0], "curve_id": r[1],
             "curve_date": r[2].isoformat() if r[2] else None,
             "tenor_years": float(r[3] or 0),
             "rate": float(r[4] or 0) / 100}
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
    """汇率数据"""
    rows = db.execute(
        text("""SELECT id, currency_pair, rate_date, bid_rate, ask_rate, mid_rate, data_source
              FROM ialm_fx_rate
              ORDER BY rate_date DESC, currency_pair LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_fx_rate")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "currency_pair": r[1],
             "rate_date": r[2].isoformat() if r[2] else None,
             "bid_rate": float(r[3] or 0),
             "ask_rate": float(r[4] or 0),
             "mid_rate": float(r[5] or 0),
             "data_source": r[6]}
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
    """股票指数数据"""
    rows = db.execute(
        text("""SELECT id, index_code, index_name, trade_date, open_price, high_price,
                     low_price, close_price, volume, amount, change_rate
              FROM ialm_equity_index
              ORDER BY trade_date DESC, index_code LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_equity_index")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "index_code": r[1], "index_name": r[2],
             "trade_date": r[3].isoformat() if r[3] else None,
             "open_price": float(r[4] or 0),
             "high_price": float(r[5] or 0),
             "low_price": float(r[6] or 0),
             "close_price": float(r[7] or 0),
             "volume": int(r[8] or 0),
             "amount": float(r[9] or 0),
             "change_rate": float(r[10] or 0)}
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
    """信用利差数据"""
    rows = db.execute(
        text("""SELECT id, rating, tenor, spread_date, spread_bps, data_source
              FROM ialm_credit_spread
              ORDER BY spread_date DESC, rating, tenor LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_credit_spread")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "rating": r[1], "tenor_years": float(r[2] or 0),
             "spread_date": r[3].isoformat() if r[3] else None,
             "spread_bps": float(r[4] or 0),
             "data_source": r[5]}
            for r in rows
        ],
    }
