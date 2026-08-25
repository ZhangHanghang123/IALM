"""IALM 期限匹配率页面修复验证"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    errors = []
    page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
    page.on("console", lambda m: errors.append(f"[console.error] {m.text}") if m.type == "error" else None)

    # 1. 访问主页 + 注入 token
    page.goto("https://wxfzhh.online/ialm/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(1500)
    login_ok = page.evaluate("""
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
                return true;
            }
            return false;
        }
    """)
    print(f"[login] {login_ok}")

    # 2. 进入期限匹配率页（BrowserRouter basename=/ialm，不是 hash 路由）
    page.goto("https://wxfzhh.online/ialm/duration-match", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/duration_01_before.png", full_page=False)

    print(f"URL: {page.url}")
    body_text = page.locator('body').inner_text()
    print(f"Body 长度: {len(body_text)}")
    print("Body 前 400 字:")
    print(body_text[:400])
    print("---")

    btns = page.locator('button').all()
    print(f"按钮数: {len(btns)}")
    for i, b in enumerate(btns[:15]):
        try:
            print(f"  [{i}] {repr(b.inner_text()[:50])}")
        except: pass

    calc_btn = None
    for b in btns:
        try:
            if '计算期限匹配率' in b.inner_text():
                calc_btn = b
                break
        except: pass

    if calc_btn:
        print("\n[click] 计算期限匹配率")
        calc_btn.click()
        page.wait_for_timeout(3500)
        page.screenshot(path="C:/银行经营/IALM/docs/duration_02_after.png", full_page=True)

        body2 = page.locator('body').inner_text()
        print(f"Body 长度(分析后): {len(body2)}")
        print("contains 'PASS':", 'PASS' in body2)
        print("contains 'FAIL':", 'FAIL' in body2)
        print("contains '0.96':", '0.96' in body2)
        print("contains 'match_ratio':", 'match_ratio' in body2)
        print("contains '门槛' or '阈值':", '阈值' in body2)
        print("\n结尾 300 字:")
        print(body2[-300:])
    else:
        print("\n[ERROR] no calculate button")

    print("\n=== JS ERRORS ===")
    for e in errors[-15:]:
        print(e)

    browser.close()
