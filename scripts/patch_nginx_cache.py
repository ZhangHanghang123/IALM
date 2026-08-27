#!/usr/bin/env python3
"""为 /ialm/ 路径块添加 no-cache header（不影响 /ialm/assets/）"""
import re
import sys

CONF = "/etc/nginx/sites-enabled/almd"

with open(CONF) as f:
    content = f.read()

# Match "location /ialm/ {" at the start of a line (NOT /ialm/assets/)
# Insert 3 cache-control headers after the opening brace
def repl(m):
    return m.group(0) + '\n        add_header Cache-Control "no-cache, no-store, must-revalidate";\n        add_header Pragma "no-cache";\n        add_header Expires "0";'

new = re.sub(r"location /ialm/ \{\s*\n", repl, content)
changes = content.count("location /ialm/ {") - new.count("location /ialm/ {")
print(f"Matched {content.count('location /ialm/ {')} /ialm/ blocks, modified {changes}")

with open(CONF, "w") as f:
    f.write(new)
print("done")
