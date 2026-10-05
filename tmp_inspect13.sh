#!/bin/bash
docker exec librechat-api sh -c 'grep -rln "think" /app/api/server/services 2>/dev/null | head -5'
echo '=== data-provider parser ==='
docker exec librechat-api sh -c 'find /app/packages /app/node_modules/@librechat -name "*.js" -path "*data-provider*" 2>/dev/null | head -5'
docker exec librechat-api sh -c 'grep -rn "think>" /app/packages/data-provider/dist/*.js 2>/dev/null | head -5'
echo '=== grep think regex in api ==='
docker exec librechat-api sh -c 'grep -rn "<think" /app/api --include=*.js -l 2>/dev/null | head -10'
