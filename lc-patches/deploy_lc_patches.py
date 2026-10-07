#!/usr/bin/env python3
"""一键发布界面补丁（零重启）：推 lc_custom.js → nginx 实时分发 → 写版本标记。

用法：
  python deploy_lc_patches.py              # 发布到生产（零重启，全程约 5 秒，用户零打断）
  python deploy_lc_patches.py --dev        # 发布到 Dev（/opt/lc-patches-dev，经 nginx 3082 分发）
  python deploy_lc_patches.py --restart    # 发布后额外重启容器（应急用；正常不需要）
  python deploy_lc_patches.py --strip-restart  # 迁移工具：剥离 index.html 内联块 + 重启（一次性）

架构（2026-10-07 零重启改造）：
  nginx 对页面 sub_filter 注入 <script src="/lc_custom.js">（no-cache），浏览器直接加载
  本文件执行全部界面定制。发布 = scp 覆盖文件，老页面由版本弹窗提示、用户点更新才刷新。
  版本标记 /picasso-version.txt（容器 dist）= PATCH_VERSION，弹窗/徽章据此判断。

旧机制（容器启动钩子 node lc_custom.js）仍保留但为 no-op；--inject-legacy 可应急回退内联注入。
发布约定：先 --dev 验证（隧道 localhost:3082），再发生产。
"""
import os, re, subprocess, sys, time

HOST = 'root@47.243.79.144'
DEV = '--dev' in sys.argv
REMOTE_JS = '/opt/lc-patches-dev/lc_custom.js' if DEV else '/opt/lc-patches/lc_custom.js'
CONTAINER = 'librechat-dev-api' if DEV else 'librechat-api'
PORT = '3082' if DEV else '443'
SELFCHECK = ('http://127.0.0.1:3082/lc_custom.js' if DEV else 'https://127.0.0.1/lc_custom.js')
CURL_K = '' if DEV else '-k '
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

rc, cur, _ = run(['ssh', '-o', 'BatchMode=yes', HOST,
                  f'curl -s -m 5 {"-k " if not DEV else ""}https://127.0.0.1/picasso-version.txt' if not DEV
                  else 'curl -s -m 5 http://127.0.0.1:3082/picasso-version.txt'])
cur = cur.strip() if rc == 0 else '?'
if cur == VER:
    print(f'[deploy{TAG}] ⚠️ 注意：线上已是 v{VER}——如果这次改了内容，用户不会收到更新提示，'
          f'请把 lc_custom.js 的 PATCH_VERSION +1 再发。')

sh(['scp', '-q', SRC, f'{HOST}:{REMOTE_JS}'])

# 自检：nginx 是否在分发新文件（no-cache 头 + 内容含本次版本号）
rc, head, err = run(['ssh', '-o', 'BatchMode=yes', HOST,
                     f'curl -s {CURL_K}-m 8 -D - -o /dev/null {SELFCHECK} | grep -i "cache-control"; '
                     f'curl -s {CURL_K}-m 8 {SELFCHECK} | grep -o "PATCH_VERSION = [0-9]*" | head -1'])
if rc != 0 or VER not in head:
    print(head or err)
    sys.exit(f'[deploy{TAG}] nginx 未分发新文件——检查 nginx 配置/是否 reload')
print(f'[deploy{TAG}] nginx 分发自检 OK（v{VER}，no-cache）')

# 版本标记（弹窗/徽章的依据）
sh(['ssh', '-o', 'BatchMode=yes', HOST,
    f'docker exec {CONTAINER} sh -c "echo {VER} > /app/client/dist/picasso-version.txt"'])

if '--strip-restart' in sys.argv:
    sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker exec {CONTAINER} node {REMOTE_JS} --strip'])
    sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker restart {CONTAINER}'])
    print(f'[deploy{TAG}] 等待容器就绪…')
    for i in range(24):
        rc, code, _ = run(['ssh', '-o', 'BatchMode=yes', HOST,
                           f'curl -s -o /dev/null -m 5 -w %{{http_code}} http://127.0.0.1:{3081 if DEV else 3080}'])
        if rc == 0 and code.strip() == '200':
            break
        time.sleep(5)
    else:
        sys.exit(f'[deploy{TAG}] 容器 120 秒未就绪，请手动检查')
    print(f'[deploy{TAG}] 迁移完成：index.html 内联块已剥离，浏览器模式接管')

if '--restart' in sys.argv:
    sh(['ssh', '-o', 'BatchMode=yes', HOST, f'docker restart {CONTAINER}'])
    print(f'[deploy{TAG}] 容器已重启（应急路径）')

print(f'[deploy{TAG}] v{VER} 发布完成（零重启）：老页面 60 秒内弹「有新版本」，'
      f'用户点「立即更新」/点右下角徽章刷新后进入新版。')
