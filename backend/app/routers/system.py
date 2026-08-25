"""
IALM 系统/字典 API
- 期限单位字典（DAY/WEEK/MONTH/QUARTER/HALF_YEAR/YEAR）
- 其他通用字典
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()


# ═══ 期限单位字典 ═══
@router.get("/period-units")
def list_period_units(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """期限单位字典列表（用于现金流期限下拉）"""
    rows = db.execute(text("""
        SELECT id, unit_code, unit_name, days_per_unit, sort_order
        FROM ialm_period_unit_dict
        WHERE is_deleted = 0
        ORDER BY sort_order, unit_code
    """)).fetchall()
    return {
        "total": len(rows),
        "items": [
            {"id": r[0], "unit_code": r[1], "unit_name": r[2],
             "days_per_unit": float(r[3] or 1), "sort_order": r[4]}
            for r in rows
        ],
    }