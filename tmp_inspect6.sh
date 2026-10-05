#!/bin/bash
python3 - <<'EOF'
s = open('/tmp/hooks.js', encoding='utf-8', errors='replace').read()
i = s.find('com_ui_thinking')
seg = s[max(0,i-9000):i-3500]
print(seg)
EOF
echo '===== locale keys ====='
docker exec librechat-api sh -c "grep -o 'com_ui_thoughts[ :]*[\`\"]*[^,\`\"]*' /app/client/dist/assets/locale-zh-Hant.*.js | head -3"
docker exec librechat-api sh -c "grep -o 'com_ui_thinking[ :]*[\`\"]*[^,\`\"]*' /app/client/dist/assets/locale-zh-Hant.*.js | head -3"
echo '===== server patch lib ====='
ls /opt/lc-patches/
cat /usr/local/bin/lc-repatch
echo '===== index.html patch marks ====='
docker exec librechat-api grep -o 'PATCH-MARK[^<]*' /app/client/dist/index.html
docker exec librechat-api grep -c 'thinking-thin-2026\|working-verbs-2026\|hide-badges-2026' /app/client/dist/index.html
