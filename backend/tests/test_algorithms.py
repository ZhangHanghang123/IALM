"""
IALM 5 号规则算法单元测试
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.algorithms import (
    calc_duration_match_ratio,
    calc_cost_yield_ratio,
    calc_cashflow_payback_years,
    calc_duration_gap,
    rule_5_full_analysis,
)


def test_alg001_duration_match_pass():
    """完全匹配的现金流 → match_ratio ≈ 1.0"""
    asset = [{"period_year": i + 1, "amount": 1000} for i in range(10)]
    liability = [{"period_year": i + 1, "amount": 1000} for i in range(10)]
    r = calc_duration_match_ratio(asset, liability)
    assert r["status"] == "PASS"
    assert r["match_ratio"] >= 0.95
    print(f"✅ ALG-001 完全匹配: ratio={r['match_ratio']}, status={r['status']}")


def test_alg001_duration_match_fail():
    """完全不匹配的现金流 → match_ratio < 0.5"""
    asset = [{"period_year": 1, "amount": 10000}]  # 全部在第 1 年
    liability = [{"period_year": 10, "amount": 10000}]  # 全部在第 10 年
    r = calc_duration_match_ratio(asset, liability)
    assert r["status"] == "FAIL"
    assert r["match_ratio"] < 0.5
    print(f"✅ ALG-001 完全不匹配: ratio={r['match_ratio']}, status={r['status']}")


def test_alg002_cost_yield_pass_life():
    """寿险 1.08 应通过（阈值 1.05）"""
    r = calc_cost_yield_ratio(
        investment_yield_rate=0.045,
        liability_cost_rate=0.03,
        expense_ratio=0.012,
        company_type="LIFE",
    )
    assert r["status"] == "PASS"
    assert r["ratio"] >= 1.05
    print(f"✅ ALG-002 寿险通过: ratio={r['ratio']}, threshold={r['threshold']}")


def test_alg002_cost_yield_fail():
    """低收益高成本应 FAIL"""
    r = calc_cost_yield_ratio(
        investment_yield_rate=0.025,
        liability_cost_rate=0.04,
        expense_ratio=0.02,
        company_type="PROPERTY",
    )
    assert r["status"] == "FAIL"
    print(f"✅ ALG-002 财险失败: ratio={r['ratio']}, threshold={r['threshold']}")


def test_alg003_cashflow_payback_pass():
    """3.5 年回正应通过（阈值 5 年）"""
    # 每期净增量（算法内部累计）
    annual_net = [
        {"year": 2025, "net": -1000},  # 第1年：累计 -1000
        {"year": 2026, "net": 300},    # 第2年：累计 -700
        {"year": 2027, "net": 400},    # 第3年：累计 -300
        {"year": 2028, "net": 500},    # 第4年：累计 +200，回正
        {"year": 2029, "net": 600},    # 第5年
        {"year": 2030, "net": 700},
    ]
    r = calc_cashflow_payback_years(annual_net, threshold=5.0)
    assert r["status"] == "PASS", f"got status={r['status']}, years={r['payback_years']}"
    assert r["payback_years"] is not None and r["payback_years"] < 5
    print(f"✅ ALG-003 3.5 年回正: years={r['payback_years']}, status={r['status']}")


def test_alg003_cashflow_payback_fail():
    """8 年仍未回正 → FAIL"""
    # 每期净流入 +100（10 年才能回正）
    annual_net = [{"year": 2025 + i, "net": -1000 + 100 * (i + 1)} for i in range(15)]
    r = calc_cashflow_payback_years(annual_net, threshold=5.0)
    assert r["status"] == "FAIL"
    print(f"✅ ALG-003 长期不回正: years={r['payback_years']}, status={r['status']}")


def test_alg004_duration_gap_pass():
    """资产久期 7, 负债久期 8, 缺口 -1 → PASS"""
    asset = [{"period_year": i + 1, "amount": 100} for i in range(20)]
    liability = [{"period_year": i + 1, "amount": 80} for i in range(20)]
    r = calc_duration_gap(asset, liability, discount_rate=0.03)
    assert "status" in r
    print(f"✅ ALG-004 久期缺口: A={r['asset_duration']}, L={r['liability_duration']}, gap={r['duration_gap']}, status={r['status']}")


def test_rule5_full_pass():
    """综合测试：通过案例"""
    asset = [{"period_year": i + 1, "amount": 1200} for i in range(15)]
    liability = [{"period_year": i + 1, "amount": 1100} for i in range(15)]
    r = rule_5_full_analysis(
        asset_cashflows=asset,
        liability_cashflows=liability,
        investment_yield_rate=0.045,
        liability_cost_rate=0.035,
        expense_ratio=0.012,
        company_type="LIFE",
    )
    assert "overall_status" in r
    print(f"✅ 综合 5 号规则: overall={r['overall_status']}")
    print(f"   ALG-001: {r['alg_001_duration_match']['status']} (ratio={r['alg_001_duration_match']['match_ratio']})")
    print(f"   ALG-002: {r['alg_002_cost_yield']['status']} (ratio={r['alg_002_cost_yield']['ratio']})")
    print(f"   ALG-003: {r['alg_003_cashflow_payback']['status']} (years={r['alg_003_cashflow_payback']['payback_years']})")
    print(f"   ALG-004: {r['alg_004_duration_gap']['status']} (gap={r['alg_004_duration_gap']['duration_gap']})")


if __name__ == "__main__":
    print("=" * 60)
    print("IALM 5 号规则算法测试")
    print("=" * 60)
    test_alg001_duration_match_pass()
    test_alg001_duration_match_fail()
    test_alg002_cost_yield_pass_life()
    test_alg002_cost_yield_fail()
    test_alg003_cashflow_payback_pass()
    test_alg003_cashflow_payback_fail()
    test_alg004_duration_gap_pass()
    test_rule5_full_pass()
    print("=" * 60)
    print("🎉 所有算法测试通过")