#!/bin/bash
docker cp librechat-api:/app/client/dist/assets/eventSelection.Bz6KLBVb.js /tmp/eventSelection.js
python3 - <<'EOF'
import re
s = open('/tmp/eventSelection.js', encoding='utf-8', errors='replace').read()
seen = set()
for m in re.finditer(r'.{100}<\\/?think.{160}', s):
    t = m.group(0)
    if t in seen: continue
    seen.add(t)
    print(t)
    print('======')
# also the THINK enum
for m in re.finditer(r'THINK[=:].{0,40}', s):
    print(m.group(0))
    print('---')
EOF
