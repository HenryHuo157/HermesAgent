#!/bin/bash
# probe-images-auth.sh — 验证带 JWT 能否读 /images/ 下文件（版本弹窗通道）
set -u
echo "=== LibreChat images 路由源码（鉴权方式）==="
docker exec librechat-api sh -c "grep -rn 'images/:filename\|/images' api/server/routes/files.js 2>/dev/null | head -5; grep -rn 'express.static' api/server/index.js api/server/routes/files.js 2>/dev/null | head -5"
echo ""
echo "=== 起一个临时测试：注册+登录拿 token，再带 token 读 images 文件 ==="
docker exec librechat-dev-api sh -c "echo probe-token-test > /app/client/public/images/picasso-probe.txt" 2>/dev/null || \
docker exec librechat-api sh -c "echo probe-token-test > /app/client/public/images/picasso-probe.txt"
PORT=\${1:-3080}
EMAIL="probe-$(date +%s)@dev.local"
REG=$(curl -s -X POST http://127.0.0.1:$PORT/api/auth/register -H 'Content-Type: application/json' \
  -d "{\"name\":\"probe\",\"username\":\"probe$(date +%s)\",\"email\":\"$EMAIL\",\"password\":\"Probe#12345678\",\"confirm_password\":\"Probe#12345678\"}")
echo "register: $(echo $REG | head -c 120)"
TOKEN=$(echo "$REG" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  LOGIN=$(curl -s -X POST http://127.0.0.1:$PORT/api/auth/login -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"Probe#12345678\"}")
  echo "login: $(echo $LOGIN | head -c 120)"
  TOKEN=$(echo "$LOGIN" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
fi
if [ -n "$TOKEN" ]; then
  curl -s -o /dev/null -w "带token GET /images/picasso-probe.txt -> HTTP %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" http://127.0.0.1:$PORT/images/picasso-probe.txt
else
  echo "没拿到 token，无法继续"
fi
docker exec librechat-dev-api rm -f /app/client/public/images/picasso-probe.txt 2>/dev/null
docker exec librechat-api rm -f /app/client/public/images/picasso-probe.txt 2>/dev/null
echo "（探测文件已清理）"
