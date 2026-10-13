#!/bin/bash
set -e
python3 - <<'PYEOF'
import re
P = '/home/dev/.hermes/config.yaml'
s = open(P, encoding='utf-8').read()

# 1) backend: local -> docker(terminal 块内)
old = "terminal:\n  backend: local\n"
assert old in s
s = s.replace(old, "terminal:\n  backend: docker\n", 1)

# 2) 恢复 container_memory 5120(撤销误改)
s = s.replace("  container_memory: 1024", "  container_memory: 5120", 1)

# 3) terminal 块加共享盘挂载(同路径,内外一致)
anchor = "  docker_mount_cwd_to_workspace: false\n"
assert anchor in s
s = s.replace(anchor, '  docker_volumes: ["/srv/hermes-share-dev:/srv/hermes-share-dev"]\n' + anchor, 1)

open(P, 'w', encoding='utf-8').write(s)
print('config.yaml: backend=docker, memory=5120 restored, volumes added')
PYEOF
# 4) 移除 .env 里多余的 TERMINAL_* 行(配置已归位 yaml,避免双源)
python3 - <<'PYEOF'
P = '/home/dev/.hermes/.env'
s = open(P, encoding='utf-8').read()
lines = [l for l in s.splitlines() if not l.startswith('TERMINAL_')]
open(P, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('.env TERMINAL_* lines removed')
PYEOF
# 5) 重启 dev 网关
sudo -u dev -H /home/dev/.local/bin/hermes gateway restart 2>&1 | tail -1
sleep 3
ss -tlnp | grep 8643 | head -1
