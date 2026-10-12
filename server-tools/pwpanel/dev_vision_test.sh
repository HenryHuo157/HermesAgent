#!/bin/bash
set -e
B=http://127.0.0.1:3081
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
TOKEN=$(curl -s -X POST $B/api/auth/login -A "$UA" -H 'Content-Type: application/json' \
  -d '{"email":"henryng@mainplan.com.hk","password":"WQz6BRtFwcFr"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
echo "1. login OK"
UP=$(curl -s -X POST $B/api/files -A "$UA" -H "Authorization: Bearer $TOKEN" \
  -F "file=@/srv/hermes-share/knife_rack_scene_v2_wood.png;type=image/png" \
  -F "endpoint=Hermes Dev" \
  -F 'width=1024' -F 'height=768')
echo "2. upload head: $(echo "$UP" | head -c 260)"
FILE_ID=$(echo "$UP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["files"][0]["file_id"])')
URL_PATH=$(echo "$UP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["files"][0]["filepath"])')
echo "3. file_id=$FILE_ID path=$URL_PATH"
echo "4. asking Hermes (SSE, may take 1-3 min), last content chunks:"
curl -s -N -X POST $B/api/ask/custom -A "$UA" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"endpoint\":\"Hermes Dev\",\"model\":\"hermes-agent\",\"text\":\"請用 vision_analyze 工具檢查這張圖片裡的砧板是什麼材質,一句話繁體中文回答。\",\"files\":[{\"file_id\":\"$FILE_ID\",\"filepath\":\"$URL_PATH\",\"width\":1024,\"height\":768}]}" \
  | grep -o '"content":"[^"]*"' | tail -6
echo "5. done"
