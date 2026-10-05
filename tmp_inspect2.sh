#!/bin/bash
echo '=== locale key for 思考過程 ==='
docker exec librechat-api grep -o '[A-Za-z_]*[ :]*[`"'"'"']思考過程' /app/client/dist/assets/locale-zh-Hant.*.js | head -3
echo
echo '=== find the key usage in main bundle ==='
KEY=dummy
docker exec librechat-api sh -c "grep -o 'com_ui_thinking_process\|thinking_process\|com_ui_thinking' /app/client/dist/assets/locale-zh-Hant.*.js | sort -u | head"
echo
echo '=== which js bundle references that key / renders think header ==='
docker exec librechat-api sh -c "grep -l 'thinking_process' /app/client/dist/assets/*.js | head"
echo
echo '=== search think-related UI strings in bundles ==='
docker exec librechat-api sh -c "grep -o 'reasoning[^,;)]\{0,60\}' /app/client/dist/assets/index.*.js | sort -u | head -40"
