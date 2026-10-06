#!/bin/bash
# verify-dev.sh — Dev 环境健康检查（picasso-dev start 之后跑）
echo "=== picasso-dev status ==="
picasso-dev status
KEY=$(grep '^API_SERVER_KEY' /home/dev/.hermes/.env | cut -d= -f2)
echo "=== Dev Hermes API (127.0.0.1:8643) ==="
curl -s -o /dev/null -w 'models 端点: HTTP %{http_code}\n' -H "Authorization: Bearer $KEY" http://127.0.0.1:8643/v1/models
echo "=== Dev LibreChat (127.0.0.1:3081) ==="
curl -s -o /dev/null -w '首页: HTTP %{http_code}\n' http://127.0.0.1:3081
curl -s http://127.0.0.1:3081 | grep -o '<title>[^<]*</title>' | head -1
echo "=== 生产未受影响检查 ==="
docker ps --filter name=librechat-api --format '{{.Names}}: {{.Status}}' | grep -v dev
ps -o pid,etime,cmd -C python | grep 'gateway run' | grep -v grep | sed 's/\(.\{90\}\).*/\1/'
