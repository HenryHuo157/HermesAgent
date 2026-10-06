#!/bin/bash
# verify-dev-e2e.sh — Dev 链路端到端验证
set -u
echo "=== 1) 修技能文件里残留的 admin 路径 ==="
n=0
while IFS= read -r f; do
  sed -i 's|/home/admin|/home/dev|g' "$f"
  n=$((n+1))
done < <(grep -rlI '/home/admin' /home/dev/.hermes/skills 2>/dev/null)
echo "改写 $n 个技能文件"
chown -R dev:dev /home/dev/.hermes/skills

KEY=$(grep '^API_SERVER_KEY' /home/dev/.hermes/.env | cut -d= -f2)

echo "=== 2) Dev LibreChat 容器 -> Dev Hermes 连通性 ==="
docker exec librechat-dev-api sh -c "wget -q -O- --header='Authorization: Bearer $KEY' http://host.docker.internal:8643/v1/models 2>&1 | head -c 200" || echo "(wget 失败)"
echo ""

echo "=== 3) Dev Hermes 真实模型调用（小请求） ==="
curl -s -m 90 http://127.0.0.1:8643/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"只回复两个字母: ok"}],"stream":false}' \
  | head -c 500
echo ""
echo "=== 完成 ==="
