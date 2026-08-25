"""IALM 算法路由：5号规则 + 14 项核心"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user
from ..models import IalmMatchAnalysis
from ..algorithms import (
    calc_duration_match_ratio,
    calc_cost_yield_ratio,
    calc_cashflow_payback_years,
    calc_duration_gap,
    rule_5_full_analysis,
)

router = APIRouter(prefix="/algorithms", tags=["算法引擎"])


class CashflowItem(BaseModel):
    period_year: int
    amount: float


class FullAnalysisRequest(BaseModel):
    company_id: int
    company_type: str = "LIFE"   # LIFE/PROPERTY/REINSURANCE/HEALTH
    asset_cashflows: List[CashflowItem]
    liability_cashflows: List[CashflowItem]
    investment_yield_rate: float       # 0.045 = 4.5%
    liability_cost_rate: float        # 0.04 = 4%
    expense_ratio: float = 0.03
    discount_rate: float = 0.03
    save_to_db: bool = False          # 是否保存到 ialm_match_analysis


@router.post("/rule5/full-analysis")
def full_analysis(
    body: FullAnalysisRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    5 号规则完整分析（ALG-001 ~ ALG-004）

    一次性输出：
    - ALG-001: 期限结构匹配率
    - ALG-002: 综合成本收益比
    - ALG-003: 现金流回正期
    - ALG-004: 久期缺口
    - 总体状态：PASS/WARN/FAIL
    """
    asset_cf = [c.dict() for c in body.asset_cashflows]
    liability_cf = [c.dict() for c in body.liability_cashflows]

    result = rule_5_full_analysis(
        asset_cashflows=asset_cf,
        liability_cashflows=liability_cf,
        investment_yield_rate=body.investment_yield_rate,
        liability_cost_rate=body.liability_cost_rate,
        expense_ratio=body.expense_ratio,
        company_type=body.company_type,
        discount_rate=body.discount_rate,
    )

    if body.save_to_db:
        # 持久化到 ialm_match_analysis
        rec = IalmMatchAnalysis(
            company_id=body.company_id,
            analysis_date=__import__("datetime").datetime.utcnow(),
            period_label="ON_DEMAND",
            duration_match_ratio=result["alg_001_duration_match"].get("match_ratio"),
            duration_match_status=result["alg_001_duration_match"].get("status"),
            cost_yield_ratio=result["alg_002_cost_yield"].get("ratio"),
            cost_yield_status=result["alg_002_cost_yield"].get("status"),
            cashflow_payback_years=result["alg_003_cashflow_payback"].get("payback_years"),
            cashflow_payback_status=result["alg_003_cashflow_payback"].get("status"),
            asset_duration=result["alg_004_duration_gap"].get("asset_duration"),
            liability_duration=result["alg_004_duration_gap"].get("liability_duration"),
            duration_gap_years=result["alg_004_duration_gap"].get("duration_gap"),
            duration_gap_status=result["alg_004_duration_gap"].get("status"),
            overall_status=result["overall_status"],
            detail_json=__import__("json").dumps(result, ensure_ascii=False),
            algorithm_version="v1.0.0",
            created_by=user.get("sub", "system"),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        result["saved_id"] = rec.id

    return result


@router.get("/rule5/algorithms")
def list_algorithms(_: dict = Depends(get_current_user)):
    """列出 14 项算法清单"""
    return {
        "algorithms": [
            {"id": "ALG-001", "name": "期限结构匹配率", "category": "5号规则", "threshold": "≥ 0.80"},
            {"id": "ALG-002", "name": "综合成本收益比", "category": "5号规则", "threshold": "寿险≥1.05/财险≥1.10"},
            {"id": "ALG-003", "name": "现金流回正期", "category": "5号规则", "threshold": "≤ 5年"},
            {"id": "ALG-004", "name": "久期与凸性", "category": "5号规则", "threshold": "缺口[-1,+1]年"},
            {"id": "ALG-005", "name": "现金流预测（蒙特卡洛）", "category": "现金流分析", "threshold": "-"},
            {"id": "ALG-006", "name": "Hull-White 利率模型", "category": "利率建模", "threshold": "-"},
            {"id": "ALG-007", "name": "压力测试", "category": "风险评估", "threshold": "6 个监管情景"},
            {"id": "ALG-008", "name": "Markowitz 最优配置", "category": "投资组合", "threshold": "-"},
            {"id": "ALG-009", "name": "Black-Litterman 配置", "category": "投资组合", "threshold": "-"},
            {"id": "ALG-010", "name": "Brinson 业绩归因", "category": "业绩评估", "threshold": "-"},
            {"id": "ALG-011", "name": "VaR / CVaR", "category": "风险评估", "threshold": "-"},
            {"id": "ALG-012", "name": "动态复制免疫", "category": "风险对冲", "threshold": "-"},
            {"id": "ALG-013", "name": "再保现金流建模", "category": "再保分析", "threshold": "-"},
            {"id": "ALG-014", "name": "久期匹配资产负债管理", "category": "组合管理", "threshold": "-"},
        ],
        "total": 14,
    }


@router.get("/rule5/aggregate-cashflows")
def aggregate_cashflows(
    company_id: int = Query(..., description="保险公司ID"),
    start_year: float = Query(0, ge=0, le=80, description="起始期数(年)"),
    end_year: float = Query(20, ge=0.1, le=80, description="结束期数(年)"),
    scenario_code: str = Query("BASE", description="情景: BASE/UP200/DOWN200/STRESS"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    从基础数据聚合现金流（供 5 号规则综合分析使用）

    资产端：在 [start_year, end_year] 区间内按 period_year 汇总 ialm_asset_cashflow
           金额(万元) → 资产收入(正数)
    负债端：在 [start_year, end_year] 区间内按 period_year 汇总 ialm_liability_cashflow
           金额(万元) → 负债支出(取绝对值，正数)

    返回：
    - asset_cashflows:     [{period_year, amount, holding_count}]
    - liability_cashflows: [{period_year, amount, policy_count}]
    - summary:             聚合统计（持仓/保单/原始记录数/总流入/总流出）
    """
    if start_year >= end_year:
        raise HTTPException(400, detail="start_year 必须小于 end_year")

    # ═══ 资产端聚合（按 period_year 汇总 COUPON+PRINCIPAL+REINVEST+TOTAL 等正流入） ═══
    asset_rows = db.execute(
        text("""SELECT
                  FLOOR(period_year) AS year_bucket,
                  SUM(amount)        AS total_amount,
                  COUNT(DISTINCT holding_id) AS holding_count,
                  COUNT(*)           AS record_count
                FROM ialm_asset_cashflow
                WHERE company_id = :cid
                  AND scenario_code = :sc
                  AND period_year >= :sy AND period_year <= :ey
                GROUP BY year_bucket
                ORDER BY year_bucket ASC"""),
        {"cid": company_id, "sc": scenario_code, "sy": start_year, "ey": end_year},
    ).fetchall()

    asset_total_in = sum(float(r[1] or 0) for r in asset_rows)

    # ═══ 负债端聚合（按 period_year 汇总，取绝对值代表支出） ═══
    liab_rows = db.execute(
        text("""SELECT
                  FLOOR(period_year) AS year_bucket,
                  SUM(amount)        AS total_amount,
                  COUNT(DISTINCT policy_id) AS policy_count,
                  COUNT(*)           AS record_count
                FROM ialm_liability_cashflow
                WHERE company_id = :cid
                  AND scenario_code = :sc
                  AND period_year >= :sy AND period_year <= :ey
                GROUP BY year_bucket
                ORDER BY year_bucket ASC"""),
        {"cid": company_id, "sc": scenario_code, "sy": start_year, "ey": end_year},
    ).fetchall()

    liab_total_out = sum(float(r[1] or 0) for r in liab_rows)

    return {
        "asset_cashflows": [
            {
                "period_year": int(r[0]),
                "amount": round(float(r[1] or 0), 4),
                "holding_count": int(r[2] or 0),
                "record_count": int(r[3] or 0),
            }
            for r in asset_rows
        ],
        "liability_cashflows": [
            {
                "period_year": int(r[0]),
                "amount": round(float(r[1] or 0), 4),
                "policy_count": int(r[2] or 0),
                "record_count": int(r[3] or 0),
            }
            for r in liab_rows
        ],
        "summary": {
            "company_id": company_id,
            "scenario_code": scenario_code,
            "start_year": start_year,
            "end_year": end_year,
            "asset_total_in": round(asset_total_in, 4),
            "liability_total_out": round(liab_total_out, 4),
            "net": round(asset_total_in - liab_total_out, 4),
            "asset_year_count": len(asset_rows),
            "liability_year_count": len(liab_rows),
        },
    }


@router.get("/rule5/history")
def analysis_history(
    company_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """历史 5 号规则分析记录"""
    q = db.query(IalmMatchAnalysis).filter(IalmMatchAnalysis.is_deleted == 0)
    if company_id:
        q = q.filter(IalmMatchAnalysis.company_id == company_id)
    total = q.count()
    items = q.order_by(IalmMatchAnalysis.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "company_id": r.company_id,
                "analysis_date": r.analysis_date.isoformat() if r.analysis_date else None,
                "duration_match_ratio": float(r.duration_match_ratio) if r.duration_match_ratio else None,
                "duration_match_status": r.duration_match_status,
                "cost_yield_ratio": float(r.cost_yield_ratio) if r.cost_yield_ratio else None,
                "cost_yield_status": r.cost_yield_status,
                "cashflow_payback_years": float(r.cashflow_payback_years) if r.cashflow_payback_years else None,
                "cashflow_payback_status": r.cashflow_payback_status,
                "duration_gap_years": float(r.duration_gap_years) if r.duration_gap_years else None,
                "duration_gap_status": r.duration_gap_status,
                "overall_status": r.overall_status,
                "algorithm_version": r.algorithm_version,
            }
            for r in items
        ],
    }