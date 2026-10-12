#!/bin/bash
set -e
# 1) dev api_server.py:修已打补丁里的 tuple 累计 bug(补丁标记已存在,无需重打)
python3 - <<'PYEOF'
P = '/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py'
s = open(P, encoding='utf-8').read()
old = "                    _emit._out_all += _item\n"
new = "                    if isinstance(_item, str):\n                        _emit._out_all += _item\n"
assert s.count(old) == 1, 'occurrences=%d' % s.count(old)
s = s.replace(old, new, 1)
open(P, 'w', encoding='utf-8').write(s)
print('dev api_server fixed')
PYEOF
# 2) user_profile_enabled -> false(dev+prod)
python3 - <<'PYEOF'
for P in ['/home/dev/.hermes/config.yaml', '/home/admin/.hermes/config.yaml']:
    s = open(P, encoding='utf-8').read()
    old = "  user_profile_enabled: true"
    assert old in s, 'user_profile_enabled not found in ' + P
    s = s.replace(old, '  user_profile_enabled: false', 1)
    open(P, 'w', encoding='utf-8').write(s)
    print('user_profile off:', P)
PYEOF
# 3) 语法校验
python3 -c "import ast; ast.parse(open('/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py', encoding='utf-8').read()); print('AST OK')"
# 4) 重启 dev 网关
sudo -u dev -H /home/dev/.local/bin/hermes gateway restart 2>&1 | tail -1
sleep 3
ss -tlnp | grep 8643 | head -1
