"""IALM 资产端管理 API"""
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/assets", tags=["资产端管理"])


# ═══ 1. 资产分类（AssetCategory） ═══
class CategoryCreate(BaseModel):
    category_code: str
    category_name: str
    parent_code: Optional[str] = ""
    risk_level: str = "LOW"
    remark: Optional[str] = ""


@router.get("/categories")
def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """资产分类列表"""
    where = ["is_deleted = 0"]
    params = {}
    if keyword:
        where.append("(category_code LIKE :kw OR category_name LIKE :kw)")
        params["kw"] = f"%{keyword}%"
    if risk_level:
        where.append("risk_level = :rl")
        params["rl"] = risk_level
    where_sql = " AND ".join(where)

    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_asset_category WHERE {where_sql}"), params).scalar() or 0
    rows = db.execute(
        text(f"""SELECT id, category_code, category_name, parent_id, category_type, risk_weight,
                     duration_default, status, created_at
              FROM ialm_asset_category WHERE {where_sql}
              ORDER BY id ASC LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    return {
        "total": total,
        "items": [
            {"id": r[0], "category_code": r[1], "category_name": r[2],
             "parent_id": r[3], "category_type": r[4],
             "risk_weight": float(r[5] or 0), "duration_default": float(r[6] or 0),
             "status": r[7], "created_at": r[8].isoformat() if r[8] else None}
            for r in rows
        ],
    }


@router.post("/categories")
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    exists = db.execute(text("SELECT id FROM ialm_asset_category WHERE category_code = :c AND is_deleted = 0"),
                         {"c": body.category_code}).fetchone()
    if exists:
        raise HTTPException(400, detail=f"分类编码 {body.category_code} 已存在")
    rid = db.execute(
        text("""INSERT INTO ialm_asset_category
              (category_code, category_name, parent_id, category_type, risk_weight,
               status, is_deleted, created_by, updated_by, created_at, updated_at)
              VALUES (:c, :n, 0, :t, 0, 1, 0, :u, :u, NOW(), NOW())"""),
        {"c": body.category_code, "n": body.category_name, "t": "OTHER",
         "u": user.get("sub", "system")},
    ).lastrowid
    db.commit()
    return {"id": rid, "category_code": body.category_code}


# ═══ 2. 资产持仓（AssetHolding） ═══
class HoldingCreate(BaseModel):
    company_id: int
    category_code: str
    holding_name: str
    book_value: float = 0
    market_value: float = 0
    coupon_rate: float = 0
    duration_years: float = 0
    maturity_date: Optional[str] = None  # YYYY-MM-DD
    rating: Optional[str] = ""
    currency: str = "CNY"


@router.get("/holdings")
def list_holdings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    company_id: Optional[int] = None,
    category_code: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    where = ["h.is_deleted = 0"]
    params = {}
    if company_id:
        where.append("h.company_id = :cid")
        params["cid"] = company_id
    if category_code:
        where.append("ac.category_code = :cc")
        params["cc"] = category_code
    where_sql = " AND ".join(where)

    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_asset_holding h WHERE {where_sql}"), params).scalar() or 0
    rows = db.execute(
        text(f"""SELECT h.id, h.company_id, c.company_short AS company_name, h.asset_code,
                     h.asset_name, ac.category_code, ac.category_name,
                     h.cost_value, h.market_value, h.coupon_rate, h.ytm,
                     h.duration_year, h.maturity_date, h.credit_rating, h.currency
              FROM ialm_asset_holding h
              LEFT JOIN ialm_insurance_company c ON c.id = h.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_asset_category ac ON ac.id = h.category_id AND ac.is_deleted = 0
              WHERE {where_sql}
              ORDER BY h.cost_value DESC LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2], "asset_code": r[3],
             "asset_name": r[4], "category_code": r[5], "category_name": r[6],
             "cost_value": float(r[7] or 0), "market_value": float(r[8] or 0),
             "coupon_rate": float(r[9] or 0), "ytm": float(r[10] or 0),
             "duration_year": float(r[11] or 0),
             "maturity_date": r[12].isoformat() if r[12] else None,
             "credit_rating": r[13], "currency": r[14]}
            for r in rows
        ],
    }


@router.post("/holdings")
def create_holding(
    body: HoldingCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    rid = db.execute(
        text("""INSERT INTO ialm_asset_holding
              (company_id, category_code, holding_name, book_value, market_value, coupon_rate,
               duration_years, maturity_date, rating, currency, status, is_deleted, created_by, updated_by, created_at, updated_at)
              VALUES (:cid, :cc, :hn, :bv, :mv, :cr, :du, :md, :rt, :cu, 1, 0, :u, :u, NOW(), NOW())"""),
        {"cid": body.company_id, "cc": body.category_code, "hn": body.holding_name,
         "bv": body.book_value, "mv": body.market_value, "cr": body.coupon_rate,
         "du": body.duration_years, "md": body.maturity_date or None,
         "rt": body.rating or "", "cu": body.currency,
         "u": user.get("sub", "system")},
    ).lastrowid
    db.commit()
    return {"id": rid, "holding_name": body.holding_name}


@router.delete("/holdings/{holding_id}")
def delete_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    db.execute(text("UPDATE ialm_asset_holding SET is_deleted = 1, updated_by = :u, updated_at = NOW() WHERE id = :id"),
               {"u": user.get("sub", "system"), "id": holding_id})
    db.commit()
    return {"deleted": True, "id": holding_id}


# ═══ 3. 资产现金流（AssetCashflow） ═══
@router.get("/cashflows")
def list_asset_cashflows(
    company_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    where = ["is_deleted = 0"]
    params = {}
    if company_id:
        where.append("company_id = :cid")
        params["cid"] = company_id
    where_sql = " AND ".join(where)

    rows = db.execute(
        text(f"""SELECT id, holding_id, company_id, asset_code, period_number, period_date,
                     period_year, cashflow_type, amount, discount_factor, present_value, scenario_code
              FROM ialm_asset_cashflow WHERE {where_sql}
              ORDER BY period_year, period_number LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_asset_cashflow WHERE {where_sql}"), params).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "holding_id": r[1], "company_id": r[2], "asset_code": r[3],
             "period_number": r[4], "period_date": r[5].isoformat() if r[5] else None,
             "period_year": float(r[6] or 0), "cashflow_type": r[7],
             "amount": float(r[8] or 0), "discount_factor": float(r[9] or 1),
             "present_value": float(r[10] or 0), "scenario_code": r[11]}
            for r in rows
        ],
    }