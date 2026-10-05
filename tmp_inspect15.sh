#!/bin/bash
docker cp librechat-api:/app/packages/data-provider/dist/index.js /tmp/dp.js
python3 - <<'EOF'
import re
s = open('/tmp/dp.js', encoding='utf-8', errors='replace').read()
seen=set()
for m in re.finditer(r'.{100}think.{140}', s):
    t=m.group(0)
    k=t[80:180]
    if k in seen: continue
    seen.add(k)
    print(t[:340]); print('======')
    if len(seen)>10: break
EOF
