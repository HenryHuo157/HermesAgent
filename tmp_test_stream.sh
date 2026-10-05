#!/bin/bash
# Direct SSE test against Hermes API server (same path LibreChat uses)
KEY=$(grep -o 'apiKey: "[^"]*"' /opt/librechat/librechat.yaml | head -1 | cut -d'"' -f2)
curl -s -N --max-time 120 http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
  -d '{"model":"hermes-agent","stream":true,"messages":[{"role":"user","content":"請用終端執行 `ls /home/admin` 並告訴我有哪幾個目錄，一句話即可"}]}' \
  > /tmp/v7_test.sse
echo "=== think/content segments (reconstructed) ==="
python3 - <<'EOF'
import json
content = ""
for line in open('/tmp/v7_test.sse', encoding='utf-8'):
    line = line.strip()
    if not line.startswith('data: ') or line == 'data: [DONE]':
        continue
    try:
        d = json.loads(line[6:])
    except Exception:
        continue
    ch = d.get('choices') or []
    if ch:
        delta = ch[0].get('delta') or {}
        content += delta.get('content') or ''
print(content[:2500])
print('...')
print('=== checks ===')
print('has <think>:', '<think>' in content)
print('has duration marker:', '思考了' in content and '秒' in content)
import re
m = re.search(r'—\s*思考了\s*(\d+)\s*秒\s*—', content)
print('marker match:', m.group(0) if m else None)
print('blockquote lines (should be 0):', sum(1 for l in content.splitlines() if l.startswith('> ')))
print('standalone checkmark lines (should be 0):', sum(1 for l in content.splitlines() if l.strip() in ('✅','✓')))
EOF
