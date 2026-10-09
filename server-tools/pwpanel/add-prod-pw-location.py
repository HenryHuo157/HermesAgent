#!/usr/bin/env python3
"""add-prod-pw-location.py — 给生产 nginx 443 块追加 /pw/ 分发到 127.0.0.1:8767（幂等、自动备份、失败还原）。"""
import shutil, subprocess, sys

CONF = '/etc/nginx/conf.d/hermes-public.conf'
BAK = CONF + '.bak-pwpanel-prod'

INSERT = '''    location /pw/ {
        proxy_pass http://127.0.0.1:8767;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

'''

conf = open(CONF, encoding='utf-8').read()
if 'proxy_pass http://127.0.0.1:8767' in conf:
    print('[ok] 生产 /pw/ location 已存在，跳过')
    sys.exit(0)

anchor = '    location = /lc_custom.js {'
pos = conf.find(anchor)  # 443 块内第一次出现（3082 块的在后半段）
if pos < 0:
    sys.exit('[fail] 未找到 443 块内 lc_custom.js location 锚点')

shutil.copy(CONF, BAK)
open(CONF, 'w', encoding='utf-8').write(conf[:pos] + INSERT + conf[pos:])
print('[done] 已插入 443 /pw/ location（备份 ' + BAK + '）')

t = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
if t.returncode != 0:
    shutil.copy(BAK, CONF)
    print('[fail] nginx -t 未通过，已还原备份：')
    print(t.stderr)
    sys.exit(1)
r = subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, text=True)
print('[done] nginx -t 通过并已 reload' if r.returncode == 0 else f'[fail] reload: {r.stderr}')
