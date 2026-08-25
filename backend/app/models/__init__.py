"""IALM ORM 模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, Index
from sqlalchemy.orm import relationship
from ..database import Base


# ═══ 公共基类：所有业务表都有的字段 ═══
class TimestampMixin:
    """时间戳 + 审计字段（与 ALMD/IALMD/ALMT 一致）"""
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer, default=1, comment="1:启用 0:禁用")
    is_deleted = Column(Integer, default=0, comment="软删除标记 0:正常 1:已删除")
    created_by = Column(String(64), default="system", comment="创建人")
    updated_by = Column(String(64), default="system", comment="更新人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


# ═══ 系统表（sys_ 前缀） ═══
class SysUser(Base, TimestampMixin):
    """系统用户"""
    __tablename__ = "sys_user"
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(64))
    email = Column(String(128))
    phone = Column(String(32))
    role = Column(String(32), default="VIEWER", comment="ALCO_CHAIR/RISK_MANAGER/ACTUARY/ASSET_MANAGER/ADMIN/VIEWER")
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(64))


# ═══ 业务表（ialm_ 前缀） ═══
class IalmInsuranceCompany(Base, TimestampMixin):
    """保险公司主档（字段与 sql/init.sql 一致）"""
    __tablename__ = "ialm_insurance_company"
    company_code = Column(String(32), unique=True, nullable=False, index=True, comment="金监局6位机构编码")
    company_name = Column(String(128), nullable=False)
    company_short = Column(String(64), default="", comment="公司简称")
    company_type = Column(String(16), comment="LIFE/PROPERTY/HEALTH/REINSURANCE/GROUP")
    legal_rep = Column(String(64), default="", comment="法定代表人")
    registered_capital = Column(Numeric(18, 2), default=0, comment="注册资本（万元）")
    established_at = Column(DateTime, comment="成立日期")
    business_scope = Column(String(512), default="", comment="经营范围")
    address = Column(String(256), default="", comment="注册地址")
    contact_phone = Column(String(20), default="", comment="联系电话")
    website = Column(String(128), default="", comment="官网")
    regulatory_rating = Column(String(16), default="", comment="A/B/C/D")
    risk_preference_id = Column(Integer, comment="风险偏好ID")


class IalmMatchAnalysis(Base, TimestampMixin):
    """资产负债匹配分析结果（5号规则三项核心指标）"""
    __tablename__ = "ialm_match_analysis"
    company_id = Column(Integer, nullable=False, index=True)
    analysis_date = Column(DateTime, nullable=False, index=True)
    period_label = Column(String(32), comment="2024Q1/2024Q4/2024FY")
    # ALG-001: 期限匹配率
    duration_match_ratio = Column(Numeric(8, 4), comment="期限结构匹配率（>=0.80）")
    duration_match_status = Column(String(16), comment="PASS/WARN/FAIL")
    # ALG-002: 综合成本收益比
    cost_yield_ratio = Column(Numeric(8, 4), comment="综合成本收益比（寿险>=1.05/财险>=1.10）")
    cost_yield_status = Column(String(16))
    # ALG-003: 现金流回正期
    cashflow_payback_years = Column(Numeric(8, 2), comment="现金流回正期（<=5年）")
    cashflow_payback_status = Column(String(16))
    # ALG-004: 久期缺口
    asset_duration = Column(Numeric(8, 4))
    liability_duration = Column(Numeric(8, 4))
    duration_gap_years = Column(Numeric(8, 4), comment="缺口（年）")
    duration_gap_status = Column(String(16))
    # 总评
    overall_status = Column(String(16), comment="PASS/WARN/FAIL")
    detail_json = Column(Text, comment="详细算法输入输出（JSON）")
    algorithm_version = Column(String(32), comment="算法版本号 v1.0.0")
    __table_args__ = (
        Index("idx_company_date", "company_id", "analysis_date"),
    )