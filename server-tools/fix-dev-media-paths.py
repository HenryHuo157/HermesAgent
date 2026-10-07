#!/usr/bin/env python3
"""fix-dev-media-paths.py — Dev 管线媒体交付路径修复（幂等）
① /srv/hermes-share → /srv/hermes-share-dev（保护已有的 -dev 后缀不被二次替换）
② https://47.243.79.144/m/ → /m/（相对链接：生产 443、Dev 3082 各自同源生效）"""
import sys

P = '/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py'
src = open(P, encoding='utf-8').read()

before_share = src.count('/srv/hermes-share')
before_url = src.count('https://47.243.79.144/m/')
already = '__DEVSHARE__' in src or src.count('/srv/hermes-share-dev') > 0 and before_share == src.count('/srv/hermes-share-dev')

src = src.replace('/srv/hermes-share-dev', '__DEVSHARE__')
src = src.replace('/srv/hermes-share', '/srv/hermes-share-dev')
src = src.replace('__DEVSHARE__', '/srv/hermes-share-dev')
src = src.replace('https://47.243.79.144/m/', '/m/')

open(P, 'w', encoding='utf-8').write(src)
import subprocess
t = subprocess.run(['python3', '-c', 'import ast,sys; ast.parse(open(sys.argv[1]).read())', P], capture_output=True, text=True)
if t.returncode != 0:
    print('[fail] 语法校验失败'); print(t.stderr); sys.exit(1)
print(f'[done] share 引用修复、prod URL→相对 {before_url} 处；语法 OK')
