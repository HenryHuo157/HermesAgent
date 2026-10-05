#!/bin/bash
python3 - <<'EOF'
import re
s = open('/tmp/hooks.js', encoding='utf-8', errors='replace').read()
# find think-tag parsing regex in client bundle
for m in re.finditer(r'.{80}<think>.{200}', s):
    print(m.group(0))
    print('======')
EOF
