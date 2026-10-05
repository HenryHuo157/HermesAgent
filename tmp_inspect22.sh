#!/bin/bash
docker exec librechat-api sh -c "grep -rln 'think' /app/api/server /app/api/app 2>/dev/null | head -20"
echo '======'
docker exec librechat-api sh -c "grep -rn 'think' /app/api/server/services/Endpoints/openAI/index.js 2>/dev/null | head -10"
