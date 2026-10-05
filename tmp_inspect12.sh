#!/bin/bash
docker exec librechat-api sh -c 'for f in /app/client/dist/assets/*.js; do case "$f" in *locale*) continue;; esac; grep -c "<think>" "$f" | grep -qv "^0$" && echo "$f"; done'
echo '=== context in each hit ==='
for f in $(docker exec librechat-api sh -c 'for f in /app/client/dist/assets/*.js; do case "$f" in *locale*) continue;; esac; c=$(grep -c "<think>" "$f"); [ "$c" != "0" ] && echo "$f"; done'); do
  echo "--- $f"
  docker cp "librechat-api:$f" /tmp/bundle.js
  python3 - <<'EOF'
import re
s = open('/tmp/bundle.js', encoding='utf-8', errors='replace').read()
for m in re.finditer(r'.{120}<think>.{140}', s):
    print(m.group(0)[:400]); print('======')
EOF
done
