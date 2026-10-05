#!/bin/bash
echo '=== find com_ui_thinking key usage in component code ==='
docker exec librechat-api sh -c "grep -l 'com_ui_thinking\b' /app/client/dist/assets/index.*.js /app/client/dist/assets/chunks*.js 2>/dev/null"
for f in $(docker exec librechat-api sh -c "grep -l 'com_ui_thinking' /app/client/dist/assets/*.js 2>/dev/null | grep -v locale"); do
  echo "--- $f ---"
  docker exec librechat-api sh -c "grep -o '.\{80\}com_ui_thinking[^A-Za-z][^;]\{0,80\}' $f | head -8"
done
echo
echo '=== lightbulb emoji location ==='
docker exec librechat-api sh -c "grep -l '\xF0\x9F\x92\xA1' /app/client/dist/assets/*.js 2>/dev/null | grep -v locale | head -5"
