#!/bin/bash
# Inspect LibreChat client bundle for reasoning UI details
echo '=== which bundles contain group/reasoning ==='
docker exec librechat-api grep -l "group/reasoning" /app/client/dist/assets/*.js 2>/dev/null
echo '=== reasoning context snippets (collapsed state, header) ==='
docker exec librechat-api grep -o '.\{160\}group\/reasoning.\{400\}' /app/client/dist/assets/index.*.js 2>/dev/null | head -c 6000
echo
echo '=== com_ui_thinking in zh-Hant locale ==='
docker exec librechat-api grep -o '"thinking[^}]*' /app/client/dist/assets/locale-zh-Hant.*.js 2>/dev/null | head -5
docker exec librechat-api sh -c 'grep -o "思考[^,\"]*" /app/client/dist/assets/locale-zh-Hant.*.js | sort -u | head -20'
