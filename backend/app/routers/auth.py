"""IALM 认证路由"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SysUser
from ..security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """登录（OAuth2 form-data 格式，与 IALMD/ALMD 一致）"""
    user = db.query(SysUser).filter(
        SysUser.username == form_data.username,
        SysUser.is_deleted == 0,
    ).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if user.status == 0:
        raise HTTPException(status_code=403, detail="账号已停用")

    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "role": user.role,
            "email": user.email,
        },
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户"""
    return current_user