from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1700, "height": 900})

    page.goto("https://wxfzhh.online/ialm/", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(1000)
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
    page.wait_for_timeout(1200)

    # 1. 保单主档 tab
    page.goto("https://wxfzhh.online/ialm/liabilities-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/liab_link_01_policies.png", full_page=False)
    print("1/3 policies tab captured")

    # 2. 点击第一个"查看现金流"
    btn = page.locator('button:has-text("查看现金流")').first
    btn.click()
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/liab_link_02_cashflows_filtered.png", full_page=True)
    print("2/3 cashflows filtered captured")

    # 3. 切换到另一个保单（终身寿险）
    try:
        page.locator('.ant-select-clear').first.click(timeout=2000)
        page.wait_for_timeout(800)
    except: pass
    page.click('.ant-select-selector', timeout=3000)
    page.wait_for_timeout(800)
    page.fill('.ant-select-selection-search-input', 'XL-2026-00008')
    page.wait_for_timeout(800)
    page.keyboard.press('Enter')
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/liab_link_03_lifetime_insurance.png", full_page=True)
    print("3/3 lifetime insurance captured")

    browser.close()