#!/bin/bash
docker cp librechat-api:/app/client/dist/assets/index.C47gUs51.js /tmp/index.js
python3 - <<'EOF'
import re
s = open('/tmp/index.js', encoding='utf-8', errors='replace').read()
pats = [r'.{60}think\\?>(.{0,120})', r'.{80}splitThink.{150}', r'.{60}THINK.{100}']
seen = set()
for p in pats:
    for m in re.finditer(p, s):
        t = m.group(0)
        if t in seen: continue
        seen.add(t)
        print(t[:400])
        print('======')
        if len(seen) > 14: break
EOF
