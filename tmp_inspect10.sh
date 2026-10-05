#!/bin/bash
python3 - <<'EOF'
import re, glob
files = glob.glob('/tmp/index.js') + glob.glob('/tmp/hooks.js')
print('also scanning all bundle names first')
import subprocess
out = subprocess.run(['docker','exec','librechat-api','sh','-c',
  "grep -l 'think' /app/client/dist/assets/*.js | grep -v locale"], capture_output=True, text=True)
print(out.stdout)
EOF
docker exec librechat-api sh -c "grep -o '.\{50\}think[^a-zA-Z][^\`]\{0,80\}' /app/client/dist/assets/chunks*.js 2>/dev/null | head -20"
docker exec librechat-api sh -c "ls /app/client/dist/assets/ | grep -i 'chunk\|common' | head"
