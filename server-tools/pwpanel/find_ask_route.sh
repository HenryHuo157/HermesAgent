#!/bin/bash
docker exec librechat-dev-api sh -c 'ls /app/api/server/routes/ | grep -i ask; echo ---; grep -rn "ask" /app/api/server/routes/index.js | head -8; echo ---; grep -rn "v1/chat/completions\|ask/custom" /app/client/src --include="*.ts" 2>/dev/null | grep -v spec | head -6'
