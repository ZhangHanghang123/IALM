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
        text(f"""SELECT id, category_code, category_name, parent_code, risk_level, status, created_at
              FROM ialm_asset_category WHERE {where_sql}
              ORDER BY id ASC LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    return {
        "total": total,
        "items": [
            {"id": r[0], "category_code": r[1], "category_name": r[2], "parent_code": r[3],
             "risk_level": r[4], "status": r[5], "created_at": r[6].isoformat() if r[6] else None}
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
              (category_code, category_name, parent_code, risk_level, status, is_deleted, created_by, updated_by, created_at, updated_at)
              VALUES (:c, :n, :p, :r, 1, 0, :u, :u, NOW(), NOW())"""),
        {"c": body.category_code, "n": body.category_name, "p": body.parent_code or "",
         "r": body.risk_level, "u": user.get("sub", "system")},
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
        where.append("h.category_code = :cc")
        params["cc"] = category_code
    where_sql = " AND ".join(where)

    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_asset_holding h WHERE {where_sql}"), params).scalar() or 0
    rows = db.execute(
        text(f"""SELECT h.id, h.company_id, c.company_short AS company_name, h.category_code,
                     h.holding_name, h.book_value, h.market_value, h.coupon_rate,
                     h.duration_years, h.maturity_date, h.rating, h.currency, h.status
              FROM ialm_asset_holding h
              LEFT JOIN ialm_insurance_company c ON c.id = h.company_id AND c.is_deleted = 0
              WHERE {where_sql}
              ORDER BY h.book_value DESC LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2], "category_code": r[3],
             "holding_name": r[4], "book_value": float(r[5] or 0), "market_value": float(r[6] or 0),
             "coupon_rate": float(r[7] or 0), "duration_years": float(r[8] or 0),
             "maturity_date": r[9].isoformat() if r[9] else None,
             "rating": r[10], "currency": r[11], "status": r[12]}
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
        text(f"""SELECT id, company_id, holding_id, period_year, period_month, amount, currency
              FROM ialm_asset_cashflow WHERE {where_sql}
              ORDER BY period_year, period_month LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_asset_cashflow WHERE {where_sql}"), params).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "holding_id": r[2],
             "period_year": r[3], "period_month": r[4], "amount": float(r[5] or 0),
             "currency": r[6]}
            for r in rows
        ],
    }