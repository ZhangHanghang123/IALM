"""Fix portfolio router field mappings to match actual DB schema."""
path = r"C:\银行经营\IALM\backend\app\routers\portfolio.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: allocations query
old = '''    rows = db.execute(
        text("""SELECT pa.id, pa.company_id, c.company_short AS company_name,
                     pa.allocation_date, pa.asset_class, pa.weight, pa.benchmark_weight, pa.expected_return
              FROM ialm_portfolio_allocation pa
              LEFT JOIN ialm_insurance_company c ON c.id = pa.company_id AND c.is_deleted = 0
              WHERE pa.is_deleted = 0
              ORDER BY pa.allocation_date DESC, pa.weight DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_portfolio_allocation WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "allocation_date": r[3].isoformat() if r[3] else None,
             "asset_class": r[4], "weight": float(r[5] or 0), "benchmark_weight": float(r[6] or 0),
             "expected_return": float(r[7] or 0)}
            for r in rows
        ],
    }'''
new = '''    rows = db.execute(
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
    }'''
assert old in content, "allocations anchor not found"
content = content.replace(old, new, 1)

# Fix 2: attributions query
old = '''    rows = db.execute(
        text("""SELECT a.id, a.company_id, c.company_short AS company_name,
                     a.attribution_date, a.asset_class,
                     a.allocation_effect, a.selection_effect, a.interaction_effect, a.total_active_return
              FROM ialm_performance_attribution a
              LEFT JOIN ialm_insurance_company c ON c.id = a.company_id AND c.is_deleted = 0
              WHERE a.is_deleted = 0
              ORDER BY a.attribution_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_performance_attribution WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "attribution_date": r[3].isoformat() if r[3] else None,
             "asset_class": r[4],
             "allocation_effect": float(r[5] or 0), "selection_effect": float(r[6] or 0),
             "interaction_effect": float(r[7] or 0), "total_active_return": float(r[8] or 0)}
            for r in rows
        ],
    }'''
new = '''    rows = db.execute(
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
    }'''
assert old in content, "attributions anchor not found"
content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")