"""IALM 后端配置（沿用 ALMD/IALMD/ALMT/CURV 架构）"""
from typing import Optional
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus, urlparse


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "IALM 保险资产负债管理智能分析平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # MySQL — URL 优先，否则用字段构建
    DATABASE_URL: Optional[str] = None
    DATABASE_URL_OVERRIDE: Optional[str] = None
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "ialm"
    MYSQL_PASSWORD: str = "Ialm@2026"
    MYSQL_DATABASE: str = "ialm_db"

    # JWT
    SECRET_KEY: str = "ialm-secret-key-please-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: str = "*"

    # DeepSeek LLM
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"

    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """优先使用 DATABASE_URL_OVERRIDE，否则 DATABASE_URL，最后用字段构建"""
        for k in ("DATABASE_URL_OVERRIDE", "DATABASE_URL"):
            url = getattr(self, k, None)
            if url:
                # 校验格式
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc and parsed.path.lstrip("/"):
                    return url
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{quote_plus(self.MYSQL_PASSWORD)}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> list:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()