#!/bin/bash
docker cp librechat-api:/app/packages/data-provider/dist/data-service-DZbh6WV_.js /tmp/ds.js
python3 - <<'EOF'
import re
s = open('/tmp/ds.js', encoding='utf-8', errors='replace').read()
print('len', len(s))
for pat in [r'<think', r'THINK']:
    print('PAT', pat)
    for m in list(re.finditer(pat, s))[:8]:
        i = m.start()
        print(repr(s[max(0,i-130):i+170])); print('---')
EOF
