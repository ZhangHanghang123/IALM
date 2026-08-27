"""Remove the /stress-run menu item since 监管情景 integrates run now."""
path = r"C:\银行经营\IALM\frontend\src\layouts\MainLayout.tsx"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
old = """      { key: '/stress-scenarios', label: '监管情景' },
      { key: '/stress-results', label: '测试结果' },
      { key: '/stress-run', label: '运行模拟' },
    ],"""
new = """      { key: '/stress-scenarios', label: '监管情景' },
      { key: '/stress-results', label: '测试结果' },
    ],"""
assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("OK")