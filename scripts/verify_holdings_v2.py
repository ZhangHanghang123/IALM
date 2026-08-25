from playwright.sync_api import sync_playwright
import httpx

# 先用 httpx 验证 API 字段
login = httpx.post('https://wxfzhh.online/ialm/api/auth/login',
                   data={'username': 'admin', 'password': 'admin123'}, timeout=10, verify=False)
token = login.json()['access_token']
hdr = {'Authorization': f'Bearer {token}'}
r = httpx.get('https://wxfzhh.online/ialm/api/assets/holdings?page_size=2', headers=hdr, verify=False, timeout=10)
items = r.json().get('items', [])
print('=== 资产持仓 API 字段 (前 2 条) ===')
for it in items:
    print(f"  company_code={it.get('company_code')} | company_full_name={it.get('company_full_name')} | company_name={it.get('company_name')}")
    print(f"  asset_code={it.get('asset_code')} | cost_value={it.get('cost_value')} | duration_year={it.get('duration_year')} | credit_rating='{it.get('credit_rating')}'")
    print()

r2 = httpx.get('https://wxfzhh.online/ialm/api/liabilities/policies?page_size=2', headers=hdr, verify=False, timeout=10)
items2 = r2.json().get('items', [])
print('=== 保单 API 字段 (前 2 条) ===')
for it in items2:
    print(f"  company_code={it.get('company_code')} | company_full_name={it.get('company_full_name')} | company_name={it.get('company_name')}")
    print(f"  product_code={it.get('product_code')} | product_name={it.get('product_name')} | sum_insured={it.get('sum_insured')}")
    print()

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

    page.goto("https://wxfzhh.online/ialm/assets-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/holdings_v2.png", full_page=False)
    print("1/2 assets-list captured")

    page.goto("https://wxfzhh.online/ialm/liabilities-list", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2500)
    page.screenshot(path="C:/银行经营/IALM/docs/liabilities_v2.png", full_page=False)
    print("2/2 liabilities-list captured")

    browser.close()