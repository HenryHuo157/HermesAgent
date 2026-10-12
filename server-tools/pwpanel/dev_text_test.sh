#!/bin/bash
set -e
B=http://127.0.0.1:3081
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36'
TOKEN=$(curl -s -X POST $B/api/auth/login -A "$UA" -H 'Content-Type: application/json' \
  -d '{"email":"henryng@mainplan.com.hk","password":"WQz6BRtFwcFr"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
echo "--- asking (SSE) ---"
curl -s -N -X POST $B/api/ask/custom -A "$UA" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"endpoint":"Hermes Dev","model":"hermes-agent","text":"請用一句繁體中文回覆:收到測試訊息即可,不要使用任何工具。"}' \
  > /tmp/sse_out.txt
echo "SSE bytes: $(wc -c < /tmp/sse_out.txt)"
echo "--- last content chunks ---"
grep -o '"content":"[^"]*"' /tmp/sse_out.txt | tail -4
echo "--- finish ---"
grep -o '"finish_reason":"[a-z]*"' /tmp/sse_out.txt | tail -1
