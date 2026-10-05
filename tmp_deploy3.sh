#!/bin/bash
set -e
echo '== 1. check hermes in-flight turns =='
ps aux | grep -c '[h]ermes' || true

echo '== 2. restore api_server.py from pre-v7 backup and apply v8 =='
cd /home/admin/.hermes/hermes-agent/gateway/platforms/
BAK=$(ls -t api_server.py.bak.* | head -1)
echo "restoring from $BAK"
cp "$BAK" api_server.py
chown admin:admin api_server.py
python3 /tmp/patch_think_v8.py
sudo -u admin python3 -m py_compile api_server.py && echo 'py_compile OK'

echo '== 3. update + re-inject lc patch =='
cp /tmp/patch_think_ui_v2.py /opt/lc-patches/patch_think_ui_v2.py
python3 /opt/lc-patches/patch_think_ui_v2.py
docker exec librechat-api grep -c 'think-ui-2026b' /app/client/dist/index.html

echo '== 4. restart hermes gateway =='
sudo -u admin -H /home/admin/.local/bin/hermes gateway restart
