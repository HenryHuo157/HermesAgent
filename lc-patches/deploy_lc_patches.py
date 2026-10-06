#!/usr/bin/env python3
"""一键部署界面补丁：把本目录的 lc_custom.js 推到服务器并让页面立即生效。

注意：LibreChat 启动时把 index.html 缓存进内存，改完必须重启容器才可见
（容器启动时会自动重打补丁，所以重启就是生效方式）。

用法：
  python deploy_lc_patches.py              # 推生产：/opt/lc-patches + librechat-api（约 40 秒）
  python deploy_lc_patches.py --dev        # 推 Dev：/opt/lc-patches-dev + librechat-dev-api
  python deploy_lc_patches.py --no-restart # 只推送+打补丁，下次容器重启时生效

发布约定：先 --dev 验证（picasso-dev start 拉起 Dev 环境后浏览器开隧道看），再推生产。
"""
import os, subprocess, sys

HOST = 'root@47.243.79.144'
DEV = '--dev' in sys.argv
REMOTE_JS = '/opt/lc-patches-dev/lc_custom.js' if DEV else '/opt/lc-patches/lc_custom.js'
CONTAINER = 'librechat-dev-api' if DEV else 'librechat-api'
TAG = '[dev] ' if DEV else ''
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lc_custom.js')

def sh(args):
    print('$', ' '.join(args))
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        sys.exit(f'[deploy] step failed: {args[0]}')

if not os.path.exists(SRC):
    sys.exit(f'[deploy] missing {SRC}')

sh(['scp', '-q', SRC, f'{HOST}:{REMOTE_JS}'])
sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker exec {CONTAINER} node {REMOTE_JS}'])

if '--no-restart' in sys.argv:
    print(f'[deploy{TAG}] staged — 下次容器重启时生效')
else:
    sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker restart {CONTAINER}'])
    print(f'[deploy{TAG}] container restarted — 约 40 秒后就绪，浏览器强刷可见')
