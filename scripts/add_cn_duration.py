"""Add Chinese reserve type mappings for liability duration estimation."""
path = r"C:\银行经营\IALM\backend\app\routers\stress.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''    duration_by_type = {
        "LIFE": 12.0,
        "UNIVERSAL_LIFE": 10.0,
        "ANNUITY": 15.0,
        "HEALTH": 4.0,
        "ACCIDENT": 2.0,
        "CLAIM": 1.0,
        "UN_EARNED_PREMIUM": 1.5,
        "UN_DERIVED": 0.5,
    }'''
new = '''    duration_by_type = {
        # 英文编码
        "LIFE": 12.0,
        "UNIVERSAL_LIFE": 10.0,
        "ANNUITY": 15.0,
        "HEALTH": 4.0,
        "ACCIDENT": 2.0,
        "CLAIM": 1.0,
        "UN_EARNED_PREMIUM": 1.5,
        "UN_DERIVED": 0.5,
        # 中文准备金类型（实际数据）
        "寿险责任准备金": 12.0,
        "健康险责任准备金": 4.0,
        "年金准备金": 15.0,
        "未到期责任准备金": 1.5,
        "未决赔款准备金": 1.0,
        "IBNR 已发生未报告准备金": 1.0,
        "长寿风险准备金": 14.0,
        "红利准备金": 8.0,
    }'''
assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")