#!/bin/bash
# probe-images-route.sh — 验证 LibreChat 是否静态服务 /images/ 下的任意文件（版本标记通道的前提）
set -u
echo "=== 生产容器 (3080) ==="
docker exec librechat-api sh -c "echo probe-$(date +%s) > /app/client/public/images/picasso-probe.txt"
sleep 1
curl -s -o /dev/null -w "GET /images/picasso-probe.txt -> HTTP %{http_code}\n" http://127.0.0.1:3080/images/picasso-probe.txt
curl -s http://127.0.0.1:3080/images/picasso-probe.txt | head -1
docker exec librechat-api rm -f /app/client/public/images/picasso-probe.txt
echo "（探测文件已清理）"
