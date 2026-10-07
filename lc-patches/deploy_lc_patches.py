#!/usr/bin/env python3
"""一键部署界面补丁：把本目录的 lc_custom.js 推到服务器并让页面生效。

注意：LibreChat 启动时把 index.html 缓存进内存，改完必须重启容器才可见
（容器启动时会自动重打补丁，所以重启就是生效方式）。

用法：
  python deploy_lc_patches.py              # 推生产：打补丁 + 重启 + 等就绪 + 写版本标记（约 1 分钟）
  python deploy_lc_patches.py --dev        # 推 Dev：/opt/lc-patches-dev + librechat-dev-api（端口 3081）
  python deploy_lc_patches.py --no-restart # 只推送+打补丁，下次容器重启时生效（不写版本标记）

版本弹窗约定：
  lc_custom.js 里的 PATCH_VERSION 就是用户所见的版本号（改内容必须 +1）。
  正常发布（重启路径）会在容器就绪后把它写进容器 /picasso-version.txt，
  所有开着的旧页面 60 秒内弹「有新版本」，用户点「立即更新」才刷新。
  --no-restart 不写标记——旧页面不会收到提示，避免提示了刷新却拿不到新版。

发布约定：先 --dev 验证（picasso-dev start 后浏览器开隧道看），再推生产。
"""
import os, re, subprocess, sys, time

HOST = 'root@47.243.79.144'
DEV = '--dev' in sys.argv
REMOTE_JS = '/opt/lc-patches-dev/lc_custom.js' if DEV else '/opt/lc-patches/lc_custom.js'
CONTAINER = 'librechat-dev-api' if DEV else 'librechat-api'
PORT = '3081' if DEV else '3080'
TAG = '[dev] ' if DEV else ''
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lc_custom.js')

def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()

def sh(args):
    print('$', ' '.join(args))
    rc, out, err = run(args)
    if out:
        print(out)
    if rc != 0:
        if err:
            print(err)
        sys.exit(f'[deploy] step failed: {args[0]}')

if not os.path.exists(SRC):
    sys.exit(f'[deploy] missing {SRC}')

src = open(SRC, encoding='utf-8').read()
m = re.search(r'PATCH_VERSION\s*=\s*(\d+)', src)
if not m:
    sys.exit('[deploy] 无法从 lc_custom.js 读到 PATCH_VERSION')
VER = m.group(1)

# 发布前线上一版（用于「版本号没变」提醒）
rc, cur, _ = run(['ssh', '-o', 'BatchMode=yes', HOST,
                  f'curl -s -m 5 http://127.0.0.1:{PORT}/picasso-version.txt'])
cur = cur.strip() if rc == 0 else '?'

sh(['scp', '-q', SRC, f'{HOST}:{REMOTE_JS}'])
sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker exec {CONTAINER} node {REMOTE_JS}'])

if '--no-restart' in sys.argv:
    print(f'[deploy{TAG}] staged（v{VER}）— 下次容器重启时生效；未写版本标记，旧页面不会收到更新提示')
else:
    sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker restart {CONTAINER}'])
    print(f'[deploy{TAG}] container restarted — 等待就绪…')
    for i in range(24):
        rc, code, _ = run(['ssh', '-o', 'BatchMode=yes', HOST,
                           f'curl -s -o /dev/null -m 5 -w %{{http_code}} http://127.0.0.1:{PORT}'])
        if rc == 0 and code.strip() == '200':
            break
        time.sleep(5)
    else:
        sys.exit(f'[deploy{TAG}] 容器 120 秒未就绪——版本标记未写入，请手动检查后补写：'
                 f'docker exec {CONTAINER} sh -c "echo {VER} > /app/client/dist/picasso-version.txt"')
    sh(['ssh', '-o', 'BatchMode=yes', HOST,
        f'docker exec {CONTAINER} sh -c "echo {VER} > /app/client/dist/picasso-version.txt"'])
    if DEV:
        rc2, out2, err2 = run(['ssh', '-o', 'BatchMode=yes', HOST, 'picasso-dev-skills'])
        print(out2 or err2)
    print(f'[deploy{TAG}] v{VER} 发布完成：容器就绪，版本标记已写入。'
          f'开着的旧页面将在 60 秒内弹「有新版本」，用户点「立即更新」才会刷新。')
    if cur == VER:
        print(f'[deploy{TAG}] ⚠️ 注意：线上原本就是 v{VER}——如果这次改了内容，用户不会收到更新提示，'
              f'请把 lc_custom.js 的 PATCH_VERSION +1 再发一次。')
