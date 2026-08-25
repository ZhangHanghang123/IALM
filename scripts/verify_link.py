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
    page.wait_for_timeout(500)

    # 资产端管理 → 默认持仓 tab
    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/link_01_holdings.png", full_page=False)
    print("1/3 holdings tab captured")

    # 点击第一个"查看现金流"
    btn = page.locator('button:has-text("查看现金流")').first
    btn.click()
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/link_02_cashflows_filtered.png", full_page=True)
    print("2/3 cashflows filtered captured")

    # 切到现金流 tab 顶部，从下拉切换到另一个持仓（股票）
    # 先点 "清除筛选"
    try:
        page.click('button:has-text("清除筛选")', timeout=3000)
        page.wait_for_timeout(1000)
    except:
        pass
    # 选择工商银行股票
    page.click('.ant-select-selector', timeout=3000)
    page.wait_for_timeout(800)
    page.fill('.ant-select-selection-search-input', '工商银行(601398)')
    page.wait_for_timeout(800)
    page.keyboard.press('Enter')
    page.wait_for_timeout(2000)
    page.screenshot(path="C:/银行经营/IALM/docs/link_03_stock_cashflows.png", full_page=True)
    print("3/3 stock cashflows captured")

    browser.close()