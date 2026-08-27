"""Fix risk router field mappings to match actual DB schema."""
path = r"C:\银行经营\IALM\backend\app\routers\risk.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: indicators query
old = '''    rows = db.execute(
        text("""SELECT ri.id, ri.company_id, c.company_short AS company_name,
                     ri.indicator_code, ri.indicator_name, ri.current_value, ri.threshold_value,
                     ri.warning_level, ri.monitor_date, ri.status
              FROM ialm_risk_indicator ri
              LEFT JOIN ialm_insurance_company c ON c.id = ri.company_id AND c.is_deleted = 0
              WHERE ri.is_deleted = 0
              ORDER BY ri.warning_level DESC, ri.current_value DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_indicator WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "indicator_code": r[3], "indicator_name": r[4], "current_value": float(r[5] or 0),
             "threshold_value": float(r[6] or 0), "warning_level": r[7],
             "monitor_date": r[8].isoformat() if r[8] else None, "status": r[9]}
            for r in rows
        ],
    }'''
new = '''    rows = db.execute(
        text("""SELECT ri.id, ri.company_id, c.company_short AS company_name,
                     ri.indicator_code, ri.indicator_name, ri.current_value,
                     ri.threshold_green, ri.threshold_yellow, ri.threshold_red,
                     ri.alert_level, ri.trend, ri.report_date, ri.extra_json
              FROM ialm_risk_indicator ri
              LEFT JOIN ialm_insurance_company c ON c.id = ri.company_id AND c.is_deleted = 0
              ORDER BY FIELD(ri.alert_level, 'RED', 'YELLOW', 'GREEN'),
                       ri.report_date DESC, ri.id DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_indicator")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "indicator_code": r[3], "indicator_name": r[4],
             "current_value": float(r[5] or 0),
             "threshold_green": float(r[6]) if r[6] is not None else None,
             "threshold_yellow": float(r[7]) if r[7] is not None else None,
             "threshold_red": float(r[8]) if r[8] is not None else None,
             "alert_level": r[9], "trend": r[10],
             "monitor_date": r[11].isoformat() if r[11] else None,
             "extra_json": r[12]}
            for r in rows
        ],
    }'''
assert old in content, "indicators anchor not found"
content = content.replace(old, new, 1)

# Fix 2: events query
old = '''    rows = db.execute(
        text("""SELECT re.id, re.company_id, c.company_short AS company_name,
                     re.event_type, re.event_level, re.title, re.description,
                     re.occurred_at, re.status, re.handler
              FROM ialm_risk_event re
              LEFT JOIN ialm_insurance_company c ON c.id = re.company_id AND c.is_deleted = 0
              WHERE re.is_deleted = 0
              ORDER BY re.occurred_at DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_event WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "event_type": r[3], "event_level": r[4], "title": r[5], "description": r[6],
             "occurred_at": r[7].isoformat() if r[7] else None,
             "status": r[8], "handler": r[9]}
            for r in rows
        ],
    }'''
new = '''    rows = db.execute(
        text("""SELECT re.id, re.company_id, c.company_short AS company_name,
                     re.event_code, re.event_name, re.event_type, re.event_level,
                     re.trigger_value, re.threshold_value, re.trigger_date,
                     re.status, re.description, re.resolution, re.resolved_at, re.resolved_by
              FROM ialm_risk_event re
              LEFT JOIN ialm_insurance_company c ON c.id = re.company_id AND c.is_deleted = 0
              ORDER BY re.trigger_date DESC, re.id DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_risk_event")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "event_code": r[3], "title": r[4] or r[3],
             "event_type": r[5], "event_level": r[6],
             "trigger_value": float(r[7] or 0), "threshold_value": float(r[8] or 0),
             "occurred_at": r[9].isoformat() if r[9] else None,
             "status": r[10], "description": r[11],
             "resolution": r[12],
             "resolved_at": r[13].isoformat() if r[13] else None,
             "resolved_by": r[14]}
            for r in rows
        ],
    }'''
assert old in content, "events anchor not found"
content = content.replace(old, new, 1)

# Fix 3: regulatory_reports query
old = '''    rows = db.execute(
        text("""SELECT rr.id, rr.company_id, c.company_short AS company_name,
                     rr.report_type, rr.report_period, rr.submit_date,
                     rr.compliance_status, rr.remark
              FROM ialm_regulatory_report rr
              LEFT JOIN ialm_insurance_company c ON c.id = rr.company_id AND c.is_deleted = 0
              WHERE rr.is_deleted = 0
              ORDER BY rr.submit_date DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_regulatory_report WHERE is_deleted = 0")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "report_type": r[3], "report_period": r[4],
             "submit_date": r[5].isoformat() if r[5] else None,
             "compliance_status": r[6], "remark": r[7]}
            for r in rows
        ],
    }'''
new = '''    rows = db.execute(
        text("""SELECT rr.id, rr.company_id, c.company_short AS company_name,
                     rr.report_type, rr.report_period, rr.report_date,
                     rr.filing_deadline, rr.file_path, rr.file_format,
                     rr.status, rr.filed_at, rr.detail_json
              FROM ialm_regulatory_report rr
              LEFT JOIN ialm_insurance_company c ON c.id = rr.company_id AND c.is_deleted = 0
              ORDER BY rr.report_date DESC, rr.id DESC LIMIT :limit OFFSET :offset"""),
        {"limit": page_size, "offset": (page - 1) * page_size},
    ).fetchall()
    total = db.execute(text("SELECT COUNT(*) FROM ialm_regulatory_report")).scalar() or 0
    return {
        "total": total,
        "items": [
            {"id": r[0], "company_id": r[1], "company_name": r[2],
             "report_type": r[3], "report_period": r[4],
             "report_date": r[5].isoformat() if r[5] else None,
             "filing_deadline": r[6].isoformat() if r[6] else None,
             "file_path": r[7], "file_format": r[8],
             "status": r[9], "compliance_status": r[9],
             "filed_at": r[10].isoformat() if r[10] else None,
             "remark": (r[11][:120] if r[11] else None)}
            for r in rows
        ],
    }'''
assert old in content, "regulatory_reports anchor not found"
content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")