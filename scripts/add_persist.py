"""Add result persistence to /stress/run."""
path = r"C:\银行经营\IALM\backend\app\routers\stress.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''    return {
        "scenario_code": row[0],
        "scenario_name": row[1],
        "company_id": body.company_id,
        "base_asset_value": A,
        "base_liability_value": L,
        "base_net_value": round(A - L, 2),
        "nav_change": round(nav_change, 2),
        "new_net_value": round(new_nav, 2),
        "scr_change_pct": round(scr_change_pct, 4),
        "passed": passed,
        "detail": detail,
    }'''
new = '''    # 持久化到 ialm_stress_result（让"测试结果"tab 有数据）
    import datetime as _dt
    asset_impact_total = sum(d.get("impact", 0) for d in detail if d.get("factor", "") in ("interest_rate", "investment_yield"))
    liability_impact_total = sum(d.get("impact", 0) for d in detail if d.get("factor", "") in ("lapse_rate",))
    solvency_before = A / body.base_scr if body.base_scr else 0
    solvency_after = (A + nav_change) / body.base_scr if body.base_scr else 0
    liquidity_gap = D_L * L - D_A * A  # 久期缺口 × 规模（经验估算）
    liquidity_gap_after = liquidity_gap + nav_change * 0.1

    user_id = user.get("id") or user.get("sub")
    try:
        user_id_int = int(user_id) if user_id is not None else None
    except (ValueError, TypeError):
        user_id_int = None

    rec = db.execute(
        text("""INSERT INTO ialm_stress_result
                (company_id, scenario_id, scenario_code, report_date,
                 asset_impact, liability_impact, nav_change, nav_change_pct,
                 solvency_ratio_before, solvency_ratio_after,
                 liquidity_gap, liquidity_gap_after, is_breached,
                 detail_json, n_paths, exec_status, exec_elapsed_ms, created_by)
                VALUES (:cid, :sid, :scode, :rd,
                        :ai, :li, :nc, :ncp,
                        :srb, :sra, :lg, :lga, :ibr,
                        :dj, 0, 'COMPLETED', 0, :uid)"""),
        {
            "cid": body.company_id, "sid": body.scenario_id, "scode": row[0],
            "rd": _dt.date.today(),
            "ai": round(asset_impact_total, 4),
            "li": round(liability_impact_total, 4),
            "nc": round(nav_change, 4),
            "ncp": round(scr_change_pct, 4),
            "srb": round(solvency_before, 4),
            "sra": round(solvency_after, 4),
            "lg": round(liquidity_gap, 4),
            "lga": round(liquidity_gap_after, 4),
            "ibr": 0 if passed else 1,
            "dj": json.dumps({
                "shocks_applied": factors,
                "impacts_per_factor": detail,
                "input_params": {
                    "asset_value": A, "liability_value": L,
                    "asset_duration": D_A, "liability_duration": D_L,
                    "base_scr": body.base_scr,
                },
            }, ensure_ascii=False),
            "uid": user_id_int,
        },
    )
    db.commit()
    saved_id = rec.lastrowid

    return {
        "id": saved_id,
        "scenario_code": row[0],
        "scenario_name": row[1],
        "company_id": body.company_id,
        "base_asset_value": A,
        "base_liability_value": L,
        "base_net_value": round(A - L, 2),
        "nav_change": round(nav_change, 2),
        "new_net_value": round(new_nav, 2),
        "scr_change_pct": round(scr_change_pct, 4),
        "passed": passed,
        "detail": detail,
    }'''
assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")