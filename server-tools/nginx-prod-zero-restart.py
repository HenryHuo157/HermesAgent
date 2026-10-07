#!/usr/bin/env python3
"""nginx-prod-zero-restart.py — 生产 nginx 接入零重启补丁分发（幂等 + 备份 + 失败自动还原）
① location / 注入 sub_filter（<script src="/lc_custom.js">）
② 新增 location = /lc_custom.js（root /opt/lc-patches，no-cache）"""
import shutil, subprocess, sys

CONF = '/etc/nginx/conf.d/hermes-public.conf'
BAK = CONF + '.bak-20261007-zero-restart'

SUBFILTER = ('        proxy_set_header Accept-Encoding "";\n'
             "        sub_filter '</head>' '<script src=\"/lc_custom.js\"></script></head>';\n"
             '        sub_filter_once on;\n'
             '        sub_filter_types text/html;\n')
ALIAS = ('    location = /lc_custom.js {\n'
         '        root /opt/lc-patches;\n'
         '        default_type application/javascript;\n'
         '        add_header Cache-Control "no-cache";\n'
         '    }\n\n')

conf = open(CONF, encoding='utf-8').read()
orig = conf
changed = []

# 只检查生产主 server 部分（location /m/ 之前），排除追加的 Dev 3082 块的干扰
head_part = conf.split('    location /m/ {')[0]
need_subfilter = "sub_filter '</head>'" not in head_part
need_alias = 'location = /lc_custom.js' not in head_part

if not need_subfilter and not need_alias:
    print('[ok] 生产 nginx 已是目标状态，跳过')
    sys.exit(0)

if need_subfilter:
    anchor = 'proxy_pass http://127.0.0.1:3080;'
    idx = conf.find(anchor)
    if idx < 0:
        print('[fail] 找不到 location / 锚点'); sys.exit(1)
    close = conf.find('\n    }', idx)
    if close < 0:
        print('[fail] 找不到 location / 结束'); sys.exit(1)
    conf = conf[:close] + '\n' + SUBFILTER.rstrip('\n') + conf[close:]
    changed.append('sub_filter')

if need_alias:
    anchor2 = '    location /m/ {'
    idx2 = conf.find(anchor2)
    if idx2 < 0:
        print('[fail] 找不到 /m/ 锚点'); sys.exit(1)
    conf = conf[:idx2] + ALIAS + conf[idx2:]
    changed.append('/lc_custom.js alias')

if conf == orig:
    print('[ok] 生产 nginx 已是目标状态，跳过')
    sys.exit(0)

shutil.copy(CONF, BAK)
open(CONF, 'w', encoding='utf-8').write(conf)
print('[done] 已修改：' + '、'.join(changed) + '（备份 ' + BAK + '）')

t = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
if t.returncode != 0:
    shutil.copy(BAK, CONF)
    print('[fail] nginx -t 未通过，已还原备份：')
    print(t.stderr)
    sys.exit(1)
r = subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, text=True)
print('[done] nginx -t 通过并已 reload' if r.returncode == 0 else f'[fail] reload: {r.stderr}')
