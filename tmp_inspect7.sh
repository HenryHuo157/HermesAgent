#!/bin/bash
python3 - <<'EOF'
s = open('/tmp/hooks.js', encoding='utf-8', errors='replace').read()
import re
# find UB definition
for m in re.finditer(r'UB=', s):
    print('UB= at', m.start(), ':', s[m.start():m.start()+420].replace('\n',' ')[:420])
    print('---')
    break
i = s.find('showThinking')
print('showThinking ctx:', s[max(0,i-260):i+260])
EOF
