#!/bin/bash
KEY=$(grep -o 'apiKey: "[^"]*"' /opt/librechat/librechat.yaml | head -1 | cut -d'"' -f2)
curl -s -N --max-time 240 http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
  -d '{"model":"hermes-agent","stream":true,"messages":[{"role":"user","content":"第一步：執行 `ls /home/admin | head -5`。第二步：先在回覆中寫出你看到的前兩個名字（這步必須在第二步命令之前完成）。第三步：執行 `ls /srv | head -5`。第四步：寫出 /srv 的前兩個名字。嚴格按順序，兩個命令之間必須先輸出第一個結果的文字。"}]}' \
  > /tmp/v8_test2.sse
python3 - <<'EOF'
import json, re
content = ""
for line in open('/tmp/v8_test2.sse', encoding='utf-8'):
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
print(content[:2500])
print('===== checks =====')
print('think opens:', content.count('<think>'))
print('think closes:', content.count('</think>'))
print('markers:', re.findall(r'思考了\s*\d+\s*秒', content))
print('standalone checkmark lines:', sum(1 for l in content.splitlines() if l.strip() == '✓'))
EOF
