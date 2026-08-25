"""IALM 保险资产负债管理智能分析平台 — FastAPI 入口"""
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.routers import auth_router, companies_router
from app.routers.algorithms import router as algorithms_router
from app.routers.assets import router as assets_router
from app.routers.liabilities import router as liabilities_router
from app.routers.market_data import router as market_data_router
from app.routers.stress import router as stress_router
from app.routers.portfolio import router as portfolio_router
from app.routers.risk import router as risk_router
from app.routers.models import router as models_router
from app.routers.system import router as system_router

# 导入模型以注册到 Base.metadata
from app.models import SysUser, IalmInsuranceCompany, IalmMatchAnalysis  # noqa: F401

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ialm")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时打印配置；关闭时 dispose 引擎"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📦 DB: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    yield
    engine.dispose()
    logger.info("👋 IALM backend stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="保险资产负债管理智能分析平台 — 5号规则三项核心监管指标 + 14 项算法引擎",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "module": "ialm",
    }


@app.get("/api/version")
def version():
    return {"version": settings.APP_VERSION}


# 路由注册（注意前缀：生产 nginx 会 strip /ialm 前缀，但保留 /api 让路径对齐 ALMD/IALMD）
app.include_router(auth_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(algorithms_router, prefix="/api")
app.include_router(assets_router, prefix="/api")
app.include_router(liabilities_router, prefix="/api")
app.include_router(market_data_router, prefix="/api")
app.include_router(stress_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(system_router, prefix="/api/system")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.DEBUG,
    )