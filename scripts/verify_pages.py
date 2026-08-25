"""IALM 资产/负债页面视觉验证"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    errors = []
    page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
    page.on("console", lambda m: errors.append(f"[console.error] {m.text}") if m.type == "error" else None)

    # 设置 token
    page.goto("https://wxfzhh.online/ialm/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(1500)
    page.evaluate("""
        async () => {
            const fd = new URLSearchParams({ username: 'admin', password: 'admin123' });
            const r = await fetch('/ialm/api/auth/login', {
                method: 'POST', body: fd,
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            const j = await r.json();
            if (j.access_token) {
                localStorage.setItem('ialm_token', j.access_token);
                localStorage.setItem('ialm_user', JSON.stringify({ username: 'admin', role: 'admin' }));
            }
        }
    """)
    print("[login] OK")

    # 1. 资产页面 - 持仓 tab
    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/assets_01_holdings.png", full_page=False)
    print("[1/4] assets-list/holdings captured")

    # 2. 资产页面 - 分类 tab
    try:
        page.click('div[role="tab"]:has-text("资产分类")', timeout=3000)
        page.wait_for_timeout(2000)
        page.screenshot(path="C:/银行经营/IALM/docs/assets_02_categories.png", full_page=False)
        print("[2/4] assets-list/categories captured")
    except Exception as e:
        print(f"[2/4] categories tab fail: {e}")

    # 3. 资产页面 - 现金流 tab
    try:
        page.click('div[role="tab"]:has-text("资产现金流")', timeout=3000)
        page.wait_for_timeout(2000)
        page.screenshot(path="C:/银行经营/IALM/docs/assets_03_cashflows.png", full_page=False)
        print("[3/4] assets-list/cashflows captured")
    except Exception as e:
        print(f"[3/4] cashflows tab fail: {e}")

    # 4. 负债页面
    page.goto("https://wxfzhh.online/ialm/liabilities-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/liabilities_01_policies.png", full_page=False)
    print("[4/4] liabilities-list/policies captured")

    # 验证页面无错误
    print("\n=== JS ERRORS ===")
    if errors:
        for e in errors[-10:]:
            print(e)
    else:
        print("  (none)")

    browser.close()
