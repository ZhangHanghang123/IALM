from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 900})

    # 注入 token（先访问 origin 再注入，不走 SPA 路由避免 navigation 竞态）
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

    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/holdings_now.png", full_page=False)
    print("captured")
    browser.close()