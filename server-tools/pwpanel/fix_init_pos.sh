#!/bin/bash
set -e
python3 - <<'PYEOF'
P = '/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py'
s = open(P, encoding='utf-8').read()

# 1) 移除错位的初始化(正文分支内,晚于首次工具活动事件)
old1 = """                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""
                    if not hasattr(_emit, "_out_all"):
                        _emit._out_all = ""
"""
new1 = """                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""
"""
assert s.count(old1) == 1
s = s.replace(old1, new1, 1)

# 2) 初始化移到 _emit 函数体最开头(任何分支之前)
old2 = '''                    if isinstance(item, tuple) and len(item) == 2 and item[0] == "__tool_progress__":'''
new2 = '''                    if not hasattr(_emit, "_out_all"):
                        _emit._out_all = ""
                    if isinstance(item, tuple) and len(item) == 2 and item[0] == "__tool_progress__":'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

open(P, 'w', encoding='utf-8').write(s)
print('dev api_server init moved')
PYEOF
python3 -c "import ast; ast.parse(open('/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py', encoding='utf-8').read()); print('AST OK')"
sudo -u dev -H /home/dev/.local/bin/hermes gateway restart 2>&1 | tail -1
sleep 3
ss -tlnp | grep 8643 | head -1
