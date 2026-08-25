"""IALM 路由集合"""
from .auth import router as auth_router
from .companies import router as companies_router

__all__ = ["auth_router", "companies_router"]