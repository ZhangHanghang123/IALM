"""IALM 模型管理 API（14 项核心算法 + 版本 + 参数）"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/models", tags=["模型管理"])


# ═══ 1. 模型定义（ModelDefinition） ═══
@router.get("/definitions")
def list_model_definitions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """14 项核心算法模型定义"""
    rows = db.execute(
        text("""SELECT id, model_code, model_name, category, priority, regulatory_code,
                     description, algorithm_summary, status
              FROM ialm_model_definition WHERE is_deleted = 0
              ORDER BY priority, model_code LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_model_definition WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "model_code": r[1], "model_name": r[2], "model_category": r[3],
             "priority": r[4], "regulatory_code": r[5],
             "description": r[6], "algorithm_summary": r[7], "status": r[8]}
            for r in rows
        ],
    }


# ═══ 2. 模型版本（ModelVersion） ═══
@router.get("/versions")
def list_model_versions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    model_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    where = ["mv.is_deleted = 0"]
    params = {}
    if model_id:
        where.append("mv.model_id = :mid")
        params["mid"] = model_id
    where_sql = " AND ".join(where)

    rows = db.execute(
        text(f"""SELECT mv.id, mv.model_id, m.model_name, mv.version_code, mv.version_name,
                     mv.release_date, mv.is_current, mv.changelog
              FROM ialm_model_version mv
              LEFT JOIN ialm_model_definition m ON m.id = mv.model_id AND m.is_deleted = 0
              WHERE {where_sql}
              ORDER BY mv.release_date DESC LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_model_version mv WHERE {where_sql}"), params).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "model_id": r[1], "model_name": r[2],
             "version_code": r[3], "version_name": r[4],
             "release_date": r[5].isoformat() if r[5] else None,
             "is_current": r[6], "changelog": r[7]}
            for r in rows
        ],
    }


# ═══ 3. 模型参数（ModelParameter） ═══
@router.get("/parameters")
def list_model_parameters(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    model_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    where = ["is_deleted = 0"]
    params = {}
    if model_id:
        where.append("model_id = :mid")
        params["mid"] = model_id
    where_sql = " AND ".join(where)

    rows = db.execute(
        text(f"""SELECT id, model_id, parameter_name, parameter_value, default_value,
                     value_type, unit, description
              FROM ialm_model_parameter WHERE {where_sql}
              ORDER BY model_id, parameter_name LIMIT :limit OFFSET :offset"""),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM ialm_model_parameter WHERE {where_sql}"), params).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "model_id": r[1], "parameter_name": r[2],
             "parameter_value": r[3], "default_value": r[4],
             "value_type": r[5], "unit": r[6], "description": r[7]}
            for r in rows
        ],
    }