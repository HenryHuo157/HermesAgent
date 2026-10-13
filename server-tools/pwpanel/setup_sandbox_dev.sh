#!/bin/bash
set -e
# ① 沙盒内存上限 5120 -> 1024(服务器总内存 3.7G,默认上限无意义)
python3 - <<'PYEOF'
P = '/home/dev/.hermes/config.yaml'
s = open(P, encoding='utf-8').read()
old = "  container_memory: 5120"
assert old in s
s = s.replace(old, "  container_memory: 1024", 1)
open(P, 'w', encoding='utf-8').write(s)
print('container_memory -> 1024')
PYEOF
# ② .env 追加 Docker 沙盒配置(挂载共享盘同路径 + 透传 FAL_KEY)
python3 - <<'PYEOF'
import json, re
P = '/home/dev/.hermes/.env'
s = open(P, encoding='utf-8').read()
m = re.search(r'^FAL_KEY=(.+)$', s, re.M)
key = m.group(1).strip() if m else ''
lines = ['',
  '# --- Docker sandbox (added 2026-10-12) ---',
  'TERMINAL_BACKEND=docker',
  'TERMINAL_DOCKER_VOLUMES=["/srv/hermes-share-dev:/srv/hermes-share-dev"]',
  'TERMINAL_DOCKER_ENV=' + json.dumps({"FAL_KEY": key}),
  'TERMINAL_DOCKER_NETWORK=true']
block = '\n'.join(lines) + '\n'
if 'TERMINAL_BACKEND=docker' not in s:
    open(P, 'a', encoding='utf-8').write(block)
print('.env sandbox config appended (FAL_KEY forwarded: %s)' % bool(key))
PYEOF
# ③ 拉取沙盒镜像(后台)
docker pull -q nikolaik/python-nodejs:python3.11-nodejs20 >/dev/null 2>&1 && echo "image pulled" || echo "image pull pending"
# ④ 重启 dev 网关加载
sudo -u dev -H /home/dev/.local/bin/hermes gateway restart 2>&1 | tail -1
sleep 4
ss -tlnp | grep 8643 | head -1
