#!/bin/bash
docker exec librechat-api sh -c 'grep -o ".\{80\}<\\\\?/think.\{150\}" /app/packages/data-provider/dist/index.js | head -6'
echo '======'
docker exec librechat-api sh -c 'grep -c "think" /app/packages/data-provider/dist/index.js; grep -o ".\{60\}thinkTag.\{120\}" /app/packages/data-provider/dist/index.js | head -4'
