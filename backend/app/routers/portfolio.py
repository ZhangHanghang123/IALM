"""IALM 投资组合 API（Markowitz + Black-Litterman + Brinson 业绩归因）"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/portfolio", tags=["投资组合"])


# ═══ 1. Markowitz 最优配置（ALG-008） ═══
class MarkowitzRequest(BaseModel):
    expected_returns: List[float]      # 各资产预期收益（小数）
    cov_matrix: List[List[float]]      # 协方差矩阵
    risk_free_rate: float = 0.025
    allow_short: bool = False


@router.post("/markowitz")
def markowitz_optimize(
    body: MarkowitzRequest,
    _: dict = Depends(get_current_user),
):
    """Markowitz 均值-方差最优投资组合（ALG-008）"""
    import numpy as np
    import cvxpy as cp

    n = len(body.expected_returns)
    if n == 0:
        return {"error": "资产数量为 0"}
    if len(body.cov_matrix) != n or any(len(row) != n for row in body.cov_matrix):
        return {"error": "协方差矩阵维度不匹配"}

    mu = np.array(body.expected_returns)
    Sigma = np.array(body.cov_matrix)
    rf = body.risk_free_rate

    w = cp.Variable(n)

    # 简化为最大化预期收益（约束：方差 <= max_var，权重和=1，w>=0）
    max_var = 0.04  # 放宽约束（标准差 0.2 = 20%）
    objective = cp.Maximize(mu @ w - rf)
    constraints = [
        cp.sum(w) == 1,
        cp.quad_form(w, cp.psd_wrap(Sigma)) <= max_var,
    ]
    if not body.allow_short:
        constraints.append(w >= 0)

    problem = cp.Problem(objective, constraints)
    try:
        problem.solve(solver=cp.CLARABEL)
        if w.value is None:
            # 退路：等权分配
            return {
                "weights": [round(1/n, 6)] * n,
                "expected_return": round(float(mu.mean()), 6),
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "status": "FALLBACK_EQUAL_WEIGHT",
            }
        weights = [round(float(x), 6) for x in w.value]
        port_return = float(mu @ w.value)
        port_var = float(w.value @ Sigma @ w.value)
        port_vol = float(np.sqrt(port_var)) if port_var > 0 else 0
        sharpe = (port_return - rf) / port_vol if port_vol > 0 else 0
        return {
            "weights": weights,
            "expected_return": round(port_return, 6),
            "volatility": round(port_vol, 6),
            "sharpe_ratio": round(sharpe, 4),
            "status": "OPTIMAL",
        }
    except Exception as e:
        return {"error": f"求解异常: {e}"}


# ═══ 2. 资产配置（PortfolioAllocation） ═══
@router.get("/allocations")
def list_allocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT pa.id, pa.company_id, c.company_short AS company_name,
                     pa.allocation_name, pa.optimization_method, pa.asset_code, ac.category_name,
                     pa.weight, pa.expected_return, pa.expected_risk, pa.sharpe_ratio,
                     pa.report_date, pa.asset_category_id
              FROM ialm_portfolio_allocation pa
              LEFT JOIN ialm_insurance_company c ON c.id = pa.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_asset_category ac ON ac.id = pa.asset_category_id AND ac.is_deleted = 0
              ORDER BY pa.report_date DESC, pa.optimization_method ASC, pa.weight DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_portfolio_allocation")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "allocation_name": r[3], "optimization_method": r[4],
             "asset_code": r[5], "asset_class": r[6],
             "weight": float(r[7] or 0),
             "expected_return": float(r[8] or 0), "expected_risk": float(r[9] or 0),
             "sharpe_ratio": float(r[10] or 0),
             "report_date": r[11].isoformat() if r[11] else None,
             "asset_category_id": r[12]}
            for r in rows
        ],
    }


# ═══ 3. 业绩归因（Brinson ALG-010） ═══
@router.get("/attributions")
def list_attributions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""SELECT a.id, a.company_id, c.company_short AS company_name,
                     a.portfolio_code, a.benchmark_code,
                     a.period_start, a.period_end, a.period_type,
                     ac.category_name AS asset_class,
                     a.allocation_effect, a.selection_effect, a.interaction_effect,
                     a.total_excess, a.asset_category_id
              FROM ialm_performance_attribution a
              LEFT JOIN ialm_insurance_company c ON c.id = a.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_asset_category ac ON ac.id = a.asset_category_id AND ac.is_deleted = 0
              ORDER BY a.period_end DESC, a.portfolio_code ASC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_performance_attribution")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "portfolio_code": r[3], "benchmark_code": r[4],
             "period_start": r[5].isoformat() if r[5] else None,
             "period_end": r[6].isoformat() if r[6] else None,
             "period_type": r[7],
             "asset_class": r[8],
             "allocation_effect": float(r[9] or 0), "selection_effect": float(r[10] or 0),
             "interaction_effect": float(r[11] or 0), "total_excess": float(r[12] or 0),
             "asset_category_id": r[13]}
            for r in rows
        ],
    }


# ═══ 4. Black-Litterman 配置（ALG-009） ═══
class BlackLittermanRequest(BaseModel):
    market_caps: List[float]          # 各资产市值权重（小数）
    cov_matrix: List[List[float]]
    expected_returns: List[float]     # 隐含均衡收益（反推）
    views: List[List[float]] = []     # 主观观点矩阵 P (k x n)
    view_returns: List[float] = []    # 观点对应收益 Q (k)
    omega: List[List[float]] = []     # 观点误差矩阵 (k x k)
    tau: float = 0.05


@router.post("/black-litterman")
def black_litterman(
    body: BlackLittermanRequest,
    _: dict = Depends(get_current_user),
):
    """Black-Litterman 配置（ALG-009）"""
    import numpy as np

    n = len(body.market_caps)
    if n == 0 or len(body.expected_returns) != n:
        return {"error": "维度错误"}
    if len(body.cov_matrix) != n:
        return {"error": "协方差矩阵维度错误"}

    w_mkt = np.array(body.market_caps)
    Sigma = np.array(body.cov_matrix)
    Pi = np.array(body.expected_returns)
    tau = body.tau

    if not body.views or len(body.views) == 0:
        # 无主观观点 → 返回均衡权重
        return {
            "weights": [round(float(x), 6) for x in w_mkt],
            "expected_returns": [round(float(x), 6) for x in Pi],
            "method": "market_implied",
        }

    P = np.array(body.views)
    Q = np.array(body.view_returns)
    Omega = np.array(body.omega) if body.omega else np.diag([0.01] * len(body.views))
    k = len(body.views)

    # Black-Litterman 公式
    # E(R) = [(τΣ)⁻¹ + P^T·Ω⁻¹·P]⁻¹·[(τΣ)⁻¹·Π + P^T·Ω⁻¹·Q]
    tau_sigma_inv = np.linalg.inv(tau * Sigma)
    pt_omega_inv = P.T @ np.linalg.inv(Omega)
    inner = tau_sigma_inv + pt_omega_inv @ P
    E_R = np.linalg.inv(inner) @ (tau_sigma_inv @ Pi + pt_omega_inv @ Q)

    # 新权重（最简单的反缩放）
    new_weights = w_mkt * (1 + tau * E_R / Sigma.diagonal())

    return {
        "weights": [round(float(x), 6) for x in new_weights],
        "expected_returns": [round(float(x), 6) for x in E_R],
        "method": "black_litterman",
        "tau": tau,
        "views_count": k,
    }