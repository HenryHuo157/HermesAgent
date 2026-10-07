#!/usr/bin/env python3
"""nginx-add-dev-m.py — Dev 3082 服务器块补 /m/ 路由（alias /srv/hermes-share-dev/，幂等）"""
import shutil, subprocess, sys

CONF = '/etc/nginx/conf.d/hermes-public.conf'
BAK = CONF + '.bak-20261007-devm'

BLOCK = ('    location /m/ {\n'
         '        alias /srv/hermes-share-dev/;\n'
         '        autoindex off;\n'
         '    }\n\n')

conf = open(CONF, encoding='utf-8').read()
dev_part = conf.split('listen 127.0.0.1:3082;')[-1]   # dev 服务器块在文件尾部
if 'alias /srv/hermes-share-dev/' in dev_part:
    print('[ok] Dev /m/ 路由已存在，跳过')
    sys.exit(0)

anchor = 'add_header Cache-Control "no-cache";\n    }'
idx = conf.rfind(anchor)   # dev 块在文件尾部，取最后一次出现
if idx < 0:
    print('[fail] 找不到 dev 块锚点'); sys.exit(1)
insert_at = idx + len(anchor)
shutil.copy(CONF, BAK)
conf = conf[:insert_at] + '\n\n' + BLOCK.rstrip('\n') + '\n' + conf[insert_at:]
open(CONF, 'w', encoding='utf-8').write(conf)
print('[done] 已插入 Dev /m/ 路由（备份 ' + BAK + '）')

t = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
if t.returncode != 0:
    shutil.copy(BAK, CONF)
    print('[fail] nginx -t 未通过，已还原：'); print(t.stderr); sys.exit(1)
r = subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, text=True)
print('[done] nginx -t 通过并已 reload' if r.returncode == 0 else f'[fail] reload: {r.stderr}')
