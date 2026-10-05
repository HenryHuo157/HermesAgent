#!/bin/bash
docker cp librechat-api:/app/client/dist/assets/hooks.BALLZO6i.js /tmp/hooks.js
python3 - <<'EOF'
import re
s = open('/tmp/hooks.js', encoding='utf-8', errors='replace').read()
i = s.find('com_ui_thinking')
print('total len', len(s), 'at', i)
print('=====CONTEXT=====')
print(s[max(0,i-4000):i+5500])
EOF
