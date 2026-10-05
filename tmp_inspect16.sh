#!/bin/bash
ls -la /tmp/dp.js 2>/dev/null || echo 'dp.js missing'
python3 - <<'EOF'
import re
s = open('/tmp/dp.js', encoding='utf-8', errors='replace').read()
print('len', len(s), 'count', s.count('think'))
idxs = [m.start() for m in re.finditer(r'think', s)][:12]
for i in idxs:
    print(repr(s[max(0,i-90):i+130]))
    print('======')
EOF
