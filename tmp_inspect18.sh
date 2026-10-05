#!/bin/bash
python3 - <<'EOF'
import re
s = open('/tmp/index.js', encoding='utf-8', errors='replace').read()
idxs = [m.start() for m in re.finditer(r'THINK', s)]
print('THINK count', len(idxs))
for i in idxs[:10]:
    print(repr(s[max(0,i-120):i+120]))
    print('======')
EOF
