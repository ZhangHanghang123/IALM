"""Fix results query column mapping."""
path = r"C:\银行经营\IALM\backend\app\routers\stress.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''    rows = db.execute(
        text("""SELECT sr.id, sr.company_id, c.company_short AS company_name,
                     sr.scenario_id, s.scenario_name,
                     sr.test_date, sr.nav_impact, sr.scr_change, sr.lcr_change, sr.passed
              FROM ialm_stress_result sr
              LEFT JOIN ialm_insurance_company c ON c.id = sr.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_stress_scenario s ON s.id = sr.scenario_id AND s.is_deleted = 0
              WHERE sr.is_deleted = 0
              ORDER BY sr.test_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_stress_result WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2], "scenario_id": r[3],
             "scenario_name": r[4], "test_date": r[5].isoformat() if r[5] else None,
             "nav_impact": float(r[6] or 0), "scr_change": float(r[7] or 0),
             "lcr_change": float(r[8] or 0), "passed": r[9]}
            for r in rows
        ],
    }'''
new = '''    rows = db.execute(
        text("""SELECT sr.id, sr.company_id, c.company_short AS company_name,
                     sr.scenario_id, s.scenario_name, s.scenario_code,
                     sr.report_date, sr.asset_impact, sr.liability_impact,
                     sr.nav_change, sr.nav_change_pct,
                     sr.solvency_ratio_before, sr.solvency_ratio_after,
                     sr.liquidity_gap, sr.liquidity_gap_after,
                     sr.is_breached, sr.exec_status, sr.exec_elapsed_ms, sr.detail_json
              FROM ialm_stress_result sr
              LEFT JOIN ialm_insurance_company c ON c.id = sr.company_id AND c.is_deleted = 0
              LEFT JOIN ialm_stress_scenario s ON s.id = sr.scenario_id AND s.is_deleted = 0
              ORDER BY sr.report_date DESC, sr.id DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_stress_result")).scalar() or 0
    return {
        "total": total,
        "items": [
            {
                "id": r[0], "company_id": r[1], "company_name": r[2],
                "scenario_id": r[3], "scenario_name": r[4], "scenario_code": r[5],
                "report_date": r[6].isoformat() if r[6] else None,
                "asset_impact": float(r[7] or 0),
                "liability_impact": float(r[8] or 0),
                "nav_change": float(r[9] or 0),
                "nav_change_pct": float(r[10] or 0),
                "solvency_ratio_before": float(r[11] or 0),
                "solvency_ratio_after": float(r[12] or 0),
                "liquidity_gap": float(r[13] or 0),
                "liquidity_gap_after": float(r[14] or 0),
                "is_breached": r[15],
                "passed": not bool(r[15]),
                "exec_status": r[16],
                "exec_elapsed_ms": int(r[17] or 0),
            }
            for r in rows
        ],
    }'''
assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")