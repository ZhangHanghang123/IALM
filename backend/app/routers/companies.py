"""IALM 保险公司管理"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import IalmInsuranceCompany
from ..security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/companies", tags=["保险公司"])


class CompanyCreate(BaseModel):
    company_code: str
    company_name: str
    company_short: Optional[str] = ""
    company_type: Optional[str] = "LIFE"
    legal_rep: Optional[str] = ""
    registered_capital: Optional[float] = 0
    established_at: Optional[str] = None
    business_scope: Optional[str] = ""
    address: Optional[str] = ""
    contact_phone: Optional[str] = ""
    website: Optional[str] = ""
    regulatory_rating: Optional[str] = ""


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    company_short: Optional[str] = None
    company_type: Optional[str] = None
    legal_rep: Optional[str] = None
    registered_capital: Optional[float] = None
    business_scope: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    regulatory_rating: Optional[str] = None
    status: Optional[int] = None


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = None,
    company_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """保险公司列表"""
    q = db.query(IalmInsuranceCompany).filter(IalmInsuranceCompany.is_deleted == 0)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            IalmInsuranceCompany.company_name.like(like),
            IalmInsuranceCompany.company_short.like(like),
            IalmInsuranceCompany.company_code.like(like),
        ))
    if company_type:
        q = q.filter(IalmInsuranceCompany.company_type == company_type)
    total = q.count()
    items = q.order_by(IalmInsuranceCompany.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "company_code": c.company_code,
                "company_name": c.company_name,
                "company_short": c.company_short,
                "company_type": c.company_type,
                "legal_rep": c.legal_rep,
                "registered_capital": float(c.registered_capital) if c.registered_capital else 0,
                "regulatory_rating": c.regulatory_rating,
                "status": c.status,
            }
            for c in items
        ],
    }


@router.post("")
def create_company(
    body: CompanyCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """新增保险公司"""
    exists = db.query(IalmInsuranceCompany).filter(
        IalmInsuranceCompany.company_code == body.company_code,
        IalmInsuranceCompany.is_deleted == 0,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail=f"机构编码 {body.company_code} 已存在")
    c = IalmInsuranceCompany(
        company_code=body.company_code,
        company_name=body.company_name,
        company_short=body.company_short or "",
        company_type=body.company_type,
        legal_rep=body.legal_rep or "",
        registered_capital=body.registered_capital or 0,
        business_scope=body.business_scope or "",
        address=body.address or "",
        contact_phone=body.contact_phone or "",
        website=body.website or "",
        regulatory_rating=body.regulatory_rating or "",
        created_by=user.get("sub", "system"),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "company_code": c.company_code}


@router.put("/{company_id}")
def update_company(
    company_id: int,
    body: CompanyUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """更新保险公司"""
    c = db.query(IalmInsuranceCompany).filter(
        IalmInsuranceCompany.id == company_id,
        IalmInsuranceCompany.is_deleted == 0,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="公司不存在")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(c, k, v)
    c.updated_by = user.get("sub", "system")
    db.commit()
    return {"id": c.id}


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """删除保险公司（软删除）"""
    c = db.query(IalmInsuranceCompany).filter(
        IalmInsuranceCompany.id == company_id,
        IalmInsuranceCompany.is_deleted == 0,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="公司不存在")
    c.is_deleted = 1
    c.updated_by = user.get("sub", "system")
    db.commit()
    return {"deleted": True, "id": company_id}