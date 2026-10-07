#!/usr/bin/env python3
"""nginx-add-dev-3082.py — 给 nginx 追加 Picasso Dev 3082 服务器块（零重启分发，与生产同构）
幂等：已存在则跳过。改前自动备份，nginx -t 失败自动还原。"""
import shutil, subprocess, sys

CONF = '/etc/nginx/conf.d/hermes-public.conf'
BAK = CONF + '.bak-20261007-zero-restart'

BLOCK = '''
# ===== Picasso Dev（仅本机回环 3082；SSH 隧道访问；零重启补丁分发，与生产同构）=====
server {
    listen 127.0.0.1:3082;

    location = /lc_custom.js {
        root /opt/lc-patches-dev;
        default_type application/javascript;
        add_header Cache-Control "no-cache";
    }

    location / {
        proxy_pass http://127.0.0.1:3081;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 3600s;
        proxy_buffering off;
        proxy_set_header Accept-Encoding "";
        sub_filter '</head>' '<script src="/lc_custom.js"></script></head>';
        sub_filter_once on;
        sub_filter_types text/html;
    }
}
'''

conf = open(CONF, encoding='utf-8').read()
if 'listen 127.0.0.1:3082' in conf:
    print('[ok] 3082 服务器块已存在，跳过')
    sys.exit(0)

shutil.copy(CONF, BAK)
open(CONF, 'a', encoding='utf-8').write(BLOCK)
print('[done] 已追加 3082 服务器块（备份 ' + BAK + '）')

t = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
if t.returncode != 0:
    shutil.copy(BAK, CONF)
    print('[fail] nginx -t 未通过，已还原备份：')
    print(t.stderr)
    sys.exit(1)
r = subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, text=True)
print('[done] nginx -t 通过并已 reload' if r.returncode == 0 else f'[fail] reload: {r.stderr}')
