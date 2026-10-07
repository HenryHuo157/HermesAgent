#!/bin/bash
# probe2.sh — 等 dev 就绪后再探测 /images/ 鉴权
set -u
PORT=${1:-3081}
echo "=== 等待 LibreChat 就绪 ==="
for i in $(seq 1 24); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT 2>/dev/null)
  [ "$code" = "200" ] && { echo "ready after ${i}x5s"; break; }
  sleep 5
done
echo "=== 容器内找 images 路由 ==="
docker exec librechat-dev-api sh -c "ls api/server/routes/ 2>/dev/null | head; grep -rn \"'/images'\" api/server/ 2>/dev/null | head -5"
echo ""
echo "=== 注册+登录+带token探测 ==="
docker exec librechat-dev-api sh -c "echo probe-token-test > /app/client/public/images/picasso-probe.txt"
STAMP=$(date +%s)
EMAIL="probe$STAMP@dev.local"
REG=$(curl -s -X POST http://127.0.0.1:$PORT/api/auth/register -H 'Content-Type: application/json' \
  -d "{\"name\":\"probe\",\"username\":\"probe$STAMP\",\"email\":\"$EMAIL\",\"password\":\"Probe#12345678\",\"confirm_password\":\"Probe#12345678\"}")
echo "register: $(echo "$REG" | head -c 200)"
TOKEN=$(echo "$REG" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  LOGIN=$(curl -s -X POST http://127.0.0.1:$PORT/api/auth/login -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"Probe#12345678\"}")
  echo "login: $(echo "$LOGIN" | head -c 200)"
  TOKEN=$(echo "$LOGIN" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
fi
if [ -n "$TOKEN" ]; then
  echo "token: ${TOKEN:0:20}..."
  curl -s -o /dev/null -w "带token GET /images/picasso-probe.txt -> HTTP %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PORT/images/picasso-probe.txt"
  curl -s -o /dev/null -w "无token GET /images/picasso-probe.txt -> HTTP %{http_code}\n" \
    "http://127.0.0.1:$PORT/images/picasso-probe.txt"
else
  echo "没拿到 token"
fi
docker exec librechat-dev-api rm -f /app/client/public/images/picasso-probe.txt
echo "（清理完成）"
