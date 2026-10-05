#!/bin/bash
docker exec librechat-api sh -c "grep -n 'think' /app/api/app/clients/BaseClient.js | head -20"
echo '=== client.js (agents) ==='
docker exec librechat-api sh -c "grep -n 'think' /app/api/server/controllers/agents/client.js | head -30"
