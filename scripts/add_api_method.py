path = r"C:\银行经营\IALM\frontend\src\api\index.ts"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
old = "  results: (params?: any) => api.get('/stress/results', { params }),\n  run: (data: any) => api.post('/stress/run', data),\n}"
new = "  results: (params?: any) => api.get('/stress/results', { params }),\n  run: (data: any) => api.post('/stress/run', data),\n  baseParameters: (params: any) => api.get('/stress/base-parameters', { params }),\n}"
assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")