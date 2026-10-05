#!/bin/bash
python3 - <<'EOF'
import re
s = open('/tmp/dp.js', encoding='utf-8', errors='replace').read()
for pat in [r'THINK\s*[:=]\s*.{0,30}', r'<think', r'splitOnThink|thinkRegex|thinkTag']:
    print('PAT', pat)
    for m in list(re.finditer(pat, s))[:8]:
        i = m.start()
        print(repr(s[max(0,i-100):i+160]))
        print('---')
EOF
