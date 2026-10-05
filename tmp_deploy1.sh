#!/bin/bash
set -e
echo '== 1. apply hermes v7 patch =='
python3 /tmp/patch_think_v7.py

echo '== 2. syntax check patched api_server.py (as admin) =='
sudo -u admin python3 -m py_compile /home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py && echo 'py_compile OK'
ls -l /home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py

echo '== 3. install lc patch + update lc-repatch =='
cp /tmp/patch_think_ui_v2.py /opt/lc-patches/patch_think_ui_v2.py
sed -i 's/patch_thinking_style\.py patch_working_verbs\.py/patch_think_ui_v2.py/' /usr/local/bin/lc-repatch
grep 'for p in' /usr/local/bin/lc-repatch

echo '== 4. run lc-repatch (injects index.html, restarts librechat-api) =='
lc-repatch

echo '== 5. restart hermes gateway =='
sudo -u admin -H /home/admin/.local/bin/hermes gateway restart

echo '== 6. verify index.html marks =='
sleep 3
docker exec librechat-api grep -o 'PATCH-MARK[^<]*' /app/client/dist/index.html
echo '--- old marks should be gone:'
docker exec librechat-api sh -c "grep -c 'thinking-thin-2026\|working-verbs-2026' /app/client/dist/index.html || true"
