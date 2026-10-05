#!/bin/bash
KEY=$(grep -o 'apiKey: "[^"]*"' /opt/librechat/librechat.yaml | head -1 | cut -d'"' -f2)
curl -s -N --max-time 180 http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
  -d '{"model":"hermes-agent","stream":true,"messages":[{"role":"user","content":"請先執行 `date`，用一句話告訴我結果，然後再執行 `whoami`，也用一句話告訴我"}]}' \
  > /tmp/v8_test.sse
python3 - <<'EOF'
import json, re
content = ""
for line in open('/tmp/v8_test.sse', encoding='utf-8'):
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
print('===== full content stream =====')
print(content[:2000])
print('===== checks =====')
print('think opens:', content.count('<think>'))
print('think closes:', content.count('</think>'))
print('markers:', re.findall(r'思考了\s*\d+\s*秒', content))
print('orphan checkmarks:', len(re.findall(r'(?:^|\n) ✓', content.replace(' ✓\n\n','X'))))
print('standalone checkmark lines:', sum(1 for l in content.splitlines() if l.strip() == '✓'))
print('blockquote lines (want 0):', sum(1 for l in content.splitlines() if l.startswith('> ')))
EOF
