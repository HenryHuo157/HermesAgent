#!/usr/bin/env python3
"""pwpanel-dev-deploy.py — 在服务器上给 Dev nginx 3082 块追加 /pw/ 分发（幂等、自动备份、失败还原）。
前置：server-tools/pwpanel/app.py 已 scp 到 /opt/pwpanel-dev/app.py"""
import shutil, subprocess, sys

CONF = '/etc/nginx/conf.d/hermes-public.conf'
MARK = 'location /pw/'
BAK = CONF + '.bak-pwpanel'

INSERT = '''    location /pw/ {
        proxy_pass http://127.0.0.1:8768;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

'''

conf = open(CONF, encoding='utf-8').read()
if MARK in conf:
    print('[ok] /pw/ location 已存在，跳过')
    sys.exit(0)

anchor = 'listen 127.0.0.1:3082;'
pos = conf.find(anchor)
if pos < 0:
    sys.exit('[fail] 未找到 3082 服务器块')
loc = conf.find('    location / {', pos)
if loc < 0:
    sys.exit('[fail] 未找到 3082 块内的 location /')

shutil.copy(CONF, BAK)
open(CONF, 'w', encoding='utf-8').write(conf[:loc] + INSERT + conf[loc:])
print('[done] 已插入 /pw/ location（备份 ' + BAK + '）')

t = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
if t.returncode != 0:
    shutil.copy(BAK, CONF)
    print('[fail] nginx -t 未通过，已还原备份：')
    print(t.stderr)
    sys.exit(1)
r = subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, text=True)
print('[done] nginx -t 通过并已 reload' if r.returncode == 0 else f'[fail] reload: {r.stderr}')
