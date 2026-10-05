#!/bin/bash
set -e
echo '== 1. restore api_server.py from latest backup and re-apply v7 =='
cd /home/admin/.hermes/hermes-agent/gateway/platforms/
BAK=$(ls -t api_server.py.bak.* | head -1)
echo "restoring from $BAK"
cp "$BAK" api_server.py
chown admin:admin api_server.py
python3 /tmp/patch_think_v7.py
sudo -u admin python3 -m py_compile api_server.py && echo 'py_compile OK'

echo '== 2. update lc patch script and re-inject (no container restart needed for index.html) =='
cp /tmp/patch_think_ui_v2.py /opt/lc-patches/patch_think_ui_v2.py
python3 /opt/lc-patches/patch_think_ui_v2.py

echo '== 3. restart hermes gateway =='
sudo -u admin -H /home/admin/.local/bin/hermes gateway restart
