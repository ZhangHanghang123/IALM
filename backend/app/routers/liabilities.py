"""IALM 负债端管理 API"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/liabilities", tags=["负债端管理"])


# ═══ 1. 产品分类（ProductCategory） ═══
@router.get("/product-categories")
def list_product_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT id, product_type_code, product_type_name, parent_id, category_level,
                     insurance_type, duration_type, payment_type, is_risk_account, sort_order
              FROM ialm_product_category WHERE is_deleted = 0
              ORDER BY id ASC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_product_category WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "product_type_code": r[1], "product_type_name": r[2], "parent_id": r[3],
             "category_level": r[4], "insurance_type": r[5], "duration_type": r[6],
             "payment_type": r[7], "is_risk_account": r[8], "sort_order": r[9]}
            for r in rows
        ],
    }


class ProductCategoryCreate(BaseModel):
    product_type_code: str
    product_type_name: str
    parent_id: int = 0
    insurance_type: str = "LIFE"


@router.post("/product-categories")
def create_product_category(
    body: ProductCategoryCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    exists = db.execute(text("SELECT id FROM ialm_product_category WHERE product_type_code = :c AND is_deleted = 0"),
                         {"c": body.product_type_code}).fetchone()
    if exists:
        raise HTTPException(400, detail=f"产品分类 {body.product_type_code} 已存在")
    rid = db.execute(
        text("""INSERT INTO ialm_product_category
              (product_type_code, product_type_name, parent_id, category_level, insurance_type,
               is_deleted, created_at, updated_at)
              VALUES (:c, :n, :p, 1, :t, 0, NOW(), NOW())"""),
        {"c": body.product_type_code, "n": body.product_type_name, "p": body.parent_id,
         "t": body.insurance_type},
    ).lastrowid
    db.commit()
    return {"id": rid, "product_type_code": body.product_type_code}


# ═══ 2. 保单主档（PolicyMaster） ═══
class PolicyCreate(BaseModel):
    policy_no: str
    company_id: int
    product_type_id: int
    product_name: str = ""
    sum_insured: float = 0
    annual_premium: float = 0
    insurance_period: int = 0


@router.get("/policies")
def list_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    where = ["p.is_deleted = 0"]
    params = {}
    if company_id:
        where.append("p.company_id = :cid")
        params["cid"] = company_id
    where_sql = " AND ".join(where)

    rows = db.execute(
        text(f"""SELECT p.id, p.policy_no, p.company_id, c.company_short AS company_name,
                     p.product_type_id, pc.product_type_name, p.sum_insured, p.annual_premium,
                     p.payment_period, p.insurance_period, p.effective_date, p.maturity_date
              FROM ialm_policy_master p
              LEFT JOIN ialm_insurance_company c ON c.id = p.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_product_category pc ON pc.id = p.product_type_id AND pc.is_deleted = 0
              WHERE {where_sql}
              ORDER BY p.sum_insured DESC LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_policy_master p WHERE {where_sql}"), params).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "policy_no": r[1], "company_id": r[2], "company_name": r[3],
             "product_type_id": r[4], "product_name": r[5],
             "sum_insured": float(r[6] or 0), "annual_premium": float(r[7] or 0),
             "payment_period": r[8], "insurance_period": r[9],
             "effective_date": r[10].isoformat() if r[10] else None,
             "maturity_date": r[11].isoformat() if r[11] else None}
            for r in rows
        ],
    }


@router.post("/policies")
def create_policy(
    body: PolicyCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    exists = db.execute(text("SELECT id FROM ialm_policy_master WHERE policy_no = :no AND is_deleted = 0"),
                         {"no": body.policy_no}).fetchone()
    if exists:
        raise HTTPException(400, detail=f"保单号 {body.policy_no} 已存在")
    rid = db.execute(
        text("""INSERT INTO ialm_policy_master
              (policy_no, company_id, product_type_id, product_name, sum_insured, annual_premium,
               payment_period, insurance_period, is_deleted, created_at, updated_at)
              VALUES (:no, :cid, :ptid, :pn, :si, :ap, 0, :ip, 0, NOW(), NOW())"""),
        {"no": body.policy_no, "cid": body.company_id, "ptid": body.product_type_id,
         "pn": body.product_name, "si": body.sum_insured, "ap": body.annual_premium,
         "ip": body.insurance_period},
    ).lastrowid
    db.commit()
    return {"id": rid, "policy_no": body.policy_no}


# ═══ 3. 负债现金流（LiabilityCashflow） ═══
@router.get("/cashflows")
def list_liability_cashflows(
    company_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    where = ["1=1"]
    params = {}
    if company_id:
        where = ["company_id = :cid"]
        params["cid"] = company_id
    where_sql = " AND ".join(where)

    rows = db.execute(
        text(f"""SELECT id, company_id, product_type_id, period_number, period_date,
                     period_year, cashflow_type, amount, discount_factor, present_value, scenario_code
              FROM ialm_liability_cashflow WHERE {where_sql}
              ORDER BY company_id, period_year, period_number LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_liability_cashflow WHERE {where_sql}"), params).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "product_type_id": r[2],
             "period_number": r[3], "period_date": r[4].isoformat() if r[4] else None,
             "period_year": float(r[5] or 0), "cashflow_type": r[6],
             "amount": float(r[7] or 0), "discount_factor": float(r[8] or 1),
             "present_value": float(r[9] or 0), "scenario_code": r[10]}
            for r in rows
        ],
    }


# ═══ 4. 准备金（Reserve） ═══
@router.get("/reserves")
def list_reserves(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT r.id, r.company_id, c.company_short, r.reserve_type,
                     r.report_date, r.amount, r.currency, r.accounting_basis, r.product_type_id
              FROM ialm_reserve r
              LEFT JOIN ialm_insurance_company c ON c.id = r.company_id AND c.is_deleted = 0
              WHERE r.is_deleted = 0
              ORDER BY r.report_date DESC, r.amount DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_reserve WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2], "reserve_type": r[3],
             "report_date": r[4].isoformat() if r[4] else None, "amount": float(r[5] or 0),
             "currency": r[6], "accounting_basis": r[7], "product_type_id": r[8]}
            for r in rows
        ],
    }


# ═══ 5. 精算假设（ActuarialAssumption） ═══
@router.get("/assumptions")
def list_assumptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT id, company_id, assumption_set_code, discount_rate,
                     effective_date, mortality_table_code, lapse_rate_code, expense_rate_code
              FROM ialm_actuarial_assumption WHERE is_deleted = 0
              ORDER BY company_id, assumption_set_code LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_actuarial_assumption WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "assumption_set_code": r[2],
             "discount_rate": float(r[3] or 0),
             "effective_date": r[4].isoformat() if r[4] else None,
             "mortality_table_code": r[5], "lapse_rate_code": r[6], "expense_rate_code": r[7]}
            for r in rows
        ],
    }