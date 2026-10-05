#!/bin/bash
KEY=$(grep -o 'apiKey: "[^"]*"' /opt/librechat/librechat.yaml | head -1 | cut -d'"' -f2)
curl -s -N --max-time 180 http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
  -d '{"model":"hermes-agent","stream":true,"messages":[{"role":"user","content":"請依次執行兩個命令：`date` 和 `whoami`，然後把兩個結果各用一句話告訴我"}]}' \
  > /tmp/v7_test2.sse
python3 - <<'EOF'
import json, re
content = ""
for line in open('/tmp/v7_test2.sse', encoding='utf-8'):
    line = line.strip()
    if not line.startswith('data: ') or line == 'data: [DONE]':
        continue
    try:
        d = json.loads(line[6:])
    except Exception:
        continue
    ch = d.get('choices') or []
    if ch:
        content += (ch[0].get('delta') or {}).get('content') or ''
i = content.find('</think>')
print('===== raw think block =====')
print(content[:i+9] if i >= 0 else content[:1500])
print('===== checks =====')
m = re.search(r'思考了\s*(\d+)\s*秒', content)
print('marker:', m.group(0) if m else None)
steps = re.findall(r'[^\n>]+…', content[:i if i>=0 else 1500])
print('tool rows:', len(steps))
print('blockquote lines (want 0):', sum(1 for l in content.splitlines() if l.startswith('> ')))
EOF
