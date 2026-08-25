"""IALM 基础数据 4 模块截图验证"""
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

    # 1. 保险公司
    page.goto("https://wxfzhh.online/ialm/companies", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/baseline_01_companies.png", full_page=False)
    print("[1/5] companies captured")

    # 2. 资产端管理（持仓 tab）
    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/baseline_02_assets_holdings.png", full_page=False)
    print("[2/5] assets/holdings captured")

    # 3. 资产分类
    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(1500)
    try:
        page.click('div[role="tab"]:has-text("资产分类")', timeout=3000)
        page.wait_for_timeout(2000)
        page.screenshot(path="C:/银行经营/IALM/docs/baseline_03_assets_categories.png", full_page=False)
        print("[3/5] assets/categories captured")
    except Exception as e:
        print(f"[3/5] categories skip: {e}")

    # 4. 负债端管理
    page.goto("https://wxfzhh.online/ialm/liabilities-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/baseline_04_liabilities.png", full_page=False)
    print("[4/5] liabilities captured")

    # 5. 市场数据
    page.goto("https://wxfzhh.online/ialm/market-data", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/baseline_05_market_data.png", full_page=False)
    print("[5/5] market-data captured")

    print("\n=== JS ERRORS ===")
    if errors:
        for e in errors[-10:]:
            print(e)
    else:
        print("  (none)")

    browser.close()
