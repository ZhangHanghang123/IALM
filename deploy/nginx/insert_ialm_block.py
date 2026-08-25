"""在 nginx almd 配置的两个 server block（443 ssl + 80 default）内都插入 IALM location"""
import re

with open('/etc/nginx/sites-enabled/almd', 'r') as f:
    src = f.read()

with open('/tmp/ialm-server-block.conf', 'r') as f:
    block = f.read()

# 找所有 server block 的结尾 } （每个 server { ... } 闭合 }）
# 找到所有 `^}` 的位置（在 server block 末尾）
# 简单做法：找所有 `}` 出现位置，逐个判断是不是 server block 末尾
# 但更简单：直接用占位符标记每个 server block 边界

server_blocks = []
i = 0
while i < len(src):
    start = src.find('server {', i)
    if start == -1:
        break
    # 找匹配的 }
    depth = 0
    j = start
    while j < len(src):
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0:
                server_blocks.append((start, j + 1))
                i = j + 1
                break
        j += 1
    else:
        break

print(f'Found {len(server_blocks)} server blocks')

# 在每个 server block 末尾前插入 ialm block
# 从后往前插，避免偏移
for start, end in reversed(server_blocks):
    block_end = end - 1  # `}` 位置
    content = src[:block_end] + block + '\n' + src[block_end:]
    src = content

with open('/etc/nginx/sites-enabled/almd', 'w') as f:
    f.write(src)

# 验证
import subprocess
result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
print('nginx -t:', result.returncode)
print(result.stdout)
print(result.stderr)