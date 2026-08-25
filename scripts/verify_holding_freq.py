from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1900, "height": 900})

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

    # 资产持仓 tab（默认）
    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/holding_freq_01_list.png", full_page=False)
    print("1/2 holdings list captured")

    # 点击第一行查看现金流 + 信息卡
    btns = page.locator('button:has-text("查看现金流")')
    btns.first.click()
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/holding_freq_02_info.png", full_page=True)
    print("2/2 info card captured")

    browser.close()