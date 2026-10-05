#!/bin/bash
echo '=== /app/api grep ==='
docker exec librechat-api sh -c "grep -rn '<think' /app/api 2>/dev/null | head -5"
echo '=== node_modules librechat-data-provider ==='
docker exec librechat-api sh -c "ls -d /app/node_modules/librechat-data-provider 2>/dev/null; grep -rln '<think' /app/node_modules/librechat-data-provider/dist 2>/dev/null | head -5"
echo '=== broad: any js in /app containing <think (limited) ==='
docker exec librechat-api sh -c "grep -rl '<think' /app --include='*.js' 2>/dev/null | grep -v 'client/dist/assets\|\.map' | head -10"
