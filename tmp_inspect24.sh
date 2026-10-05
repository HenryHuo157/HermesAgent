#!/bin/bash
echo '=== BaseClient around 1560-1700 ==='
docker exec librechat-api sh -c "sed -n '1560,1700p' /app/api/app/clients/BaseClient.js"
