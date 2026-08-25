from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1700, "height": 900})

    page.goto("https://wxfzhh.online/ialm/", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=10000)
    page.evaluate("""
        async () => {
            const fd = new URLSearchParams({ username: 'admin', password: 'admin123' });
            const r = await fetch('/ialm/api/auth/login', {
                method: 'POST', body: fd,
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            const j = await r.json();
            if (j.access_token) localStorage.setItem('ialm_token', j.access_token);
            return 'ok';
        }
    """)
    page.wait_for_timeout(800)

    # 1. 同业存单
    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.click('div[role="tab"]:has-text("资产现金流")', timeout=3000)
    page.wait_for_timeout(1500)
    page.click('.ant-select-selector', timeout=3000)
    page.wait_for_timeout(800)
    page.fill('.ant-select-selection-search-input', '同业存单')
    page.wait_for_timeout(800)
    page.keyboard.press('Enter')
    page.wait_for_timeout(2000)
    page.screenshot(path="C:/银行经营/IALM/docs/period_unit_01_cd.png", full_page=True)
    print("1/3 同业存单 captured")

    # 2. 国债
    # 清除旧选择
    try:
        page.locator('.ant-select-clear').first.click(timeout=2000)
        page.wait_for_timeout(800)
    except: pass
    page.click('.ant-select-selector', timeout=3000)
    page.wait_for_timeout(800)
    page.fill('.ant-select-selection-search-input', '24 国债 010107')
    page.wait_for_timeout(800)
    page.keyboard.press('Enter')
    page.wait_for_timeout(2000)
    page.screenshot(path="C:/银行经营/IALM/docs/period_unit_02_bond.png", full_page=True)
    print("2/3 国债 captured")

    # 3. 负债现金流（含字典说明）
    page.goto("https://wxfzhh.online/ialm/liabilities-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.click('div[role="tab"]:has-text("负债现金流")', timeout=3000)
    page.wait_for_timeout(1500)
    page.screenshot(path="C:/银行经营/IALM/docs/period_unit_03_liab.png", full_page=True)
    print("3/3 负债 captured")

    browser.close()