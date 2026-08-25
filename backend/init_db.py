"""
IALM 数据库初始化脚本
===================

执行流程：
1. 读取 .env 配置
2. 创建 ialm_db 数据库（如果不存在）
3. 创建所有 ORM 表（46 张）
4. 导入种子数据（角色/权限/管理员账号/14 算法模型）
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import engine, Base
from app.security import hash_password

# 导入所有模型（必须显式 import 才能注册到 Base.metadata）
from app.models import SysUser, IalmInsuranceCompany, IalmMatchAnalysis  # noqa


def ensure_database():
    """创建 ialm_db 库（如不存在）"""
    # 先连无库名连接
    server_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:"
        f"{os.getenv('MYSQL_PASSWORD', settings.MYSQL_PASSWORD).replace('@', '%40')}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/?charset=utf8mb4"
    )
    s_engine = create_engine(server_url, pool_pre_ping=True)
    with s_engine.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
        conn.commit()
    s_engine.dispose()
    print(f"✅ 数据库 {settings.MYSQL_DATABASE} 已就绪")


def create_tables():
    """
    跳过 — 表结构由 sql/init.sql 提供（46 张表 + 种子数据 + 索引）
    ORM 模型只用于业务代码，结构对齐 sql/init.sql
    """
    # Base.metadata.create_all(bind=engine)  # 不再调用，避免与 SQL DDL 字段冲突
    # SQL 已通过 init.sql 导入完成
    pass


def seed_data():
    """种子数据"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. 管理员账号
        admin = session.query(SysUser).filter(SysUser.username == "admin").first()
        if not admin:
            admin = SysUser(
                username="admin",
                password_hash=hash_password("admin123"),
                real_name="系统管理员",
                email="admin@ialm.com",
                role="ADMIN",
                status=1,
                created_by="system",
            )
            session.add(admin)
            print("✅ 创建 admin 账号（admin / admin123）")
        else:
            print("ℹ️ admin 已存在，跳过")

        # 2. 示例保险公司（与 IALMD 共享金管局机构编码）
        sample_companies = [
            ("000001", "中国人寿保险股份有限公司", "国寿", "LIFE", 28260000.00, 1),
            ("000002", "中国平安人寿保险股份有限公司", "平安", "LIFE", 3380000.00, 1),
            ("000003", "中国太平洋人寿保险股份有限公司", "太保", "LIFE", 8420000.00, 1),
            ("000004", "新华人寿保险股份有限公司", "新华", "LIFE", 3115000.00, 1),
            ("000005", "中国人寿财产保险股份有限公司", "国寿财险", "PROPERTY", 1880000.00, 0),
            ("000006", "中国平安财产保险股份有限公司", "平安财险", "PROPERTY", 2100000.00, 0),
            ("000007", "中国太平洋财产保险股份有限公司", "太保财险", "PROPERTY", 1947000.00, 0),
            ("000008", "中国人寿再保险有限责任公司", "中再寿险", "REINSURANCE", 4500000.00, 0),
            ("000009", "中国财产再保险有限责任公司", "中再财险", "REINSURANCE", 1100000.00, 0),
            ("000010", "泰康人寿保险有限责任公司", "泰康", "LIFE", 9999997.00, 0),
        ]
        for code, name, short, ctype, capital, listed in sample_companies:
            exists = session.query(IalmInsuranceCompany).filter(
                IalmInsuranceCompany.company_code == code
            ).first()
            if not exists:
                c = IalmInsuranceCompany(
                    company_code=code,
                    company_name=name,
                    short_name=short,
                    company_type=ctype,
                    registered_capital=capital,
                    is_listed=listed,
                    created_by="system",
                )
                session.add(c)
        print(f"✅ 种子保险公司 {len(sample_companies)} 家")

        session.commit()
        print("✅ 所有种子数据已落库")

    except Exception as e:
        session.rollback()
        print(f"❌ 种子数据失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print(f"🔧 IALM 数据库初始化 - {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    print("=" * 60)
    ensure_database()
    create_tables()
    seed_data()
    print("=" * 60)
    print("🎉 初始化完成")