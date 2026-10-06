#!/bin/bash
# build-dev-lc.sh — 一次性搭建 Dev LibreChat 栈（root 执行；幂等）
set -euo pipefail

mkdir -p /opt/lc-dev/images /opt/lc-dev/data-node
cp /tmp/lc-dev-compose.yml /opt/lc-dev/docker-compose.yml

# .env：全新随机密钥（与生产完全独立）
if [ ! -f /opt/lc-dev/.env ]; then
  {
    echo "HOST=0.0.0.0"
    echo "PORT=3080"
    echo "MONGO_URI=mongodb://mongodb:27017/LibreChatDev"
    echo "SECRET_KEY=$(openssl rand -hex 32)"
    echo "APP_TITLE=畢卡索 Dev"
    echo "SCHEDULES_SINGLE_PROCESS=true"
    echo "ALLOW_REGISTRATION=true"
    echo "EMAIL_ENABLED=false"
    echo "ALLOW_EMAIL_VERIFICATION=false"
    echo "CREDS_KEY=$(openssl rand -hex 32)"
    echo "CREDS_IV=$(openssl rand -hex 16)"
    echo "JWT_SECRET=$(openssl rand -hex 32)"
    echo "JWT_REFRESH_SECRET=$(openssl rand -hex 32)"
  } > /opt/lc-dev/.env
  chmod 600 /opt/lc-dev/.env
fi

# librechat.yaml：从生产派生（apiKey 继承，端口 8643，名称加 Dev）
sed -e 's/8642/8643/' -e 's/name: "Hermes"/name: "Hermes Dev"/' \
  /opt/librechat/librechat.yaml > /opt/lc-dev/librechat.yaml

chown -R 1000:1000 /opt/lc-dev/images

# 独立补丁目录（dev 上的 UI 实验不影响生产补丁）
rm -rf /opt/lc-patches-dev
cp -a /opt/lc-patches /opt/lc-patches-dev

# 控制脚本
cp /tmp/picasso-dev.sh /usr/local/bin/picasso-dev
cp /tmp/hermes-repatch-dev.sh /usr/local/bin/hermes-repatch-dev
chmod +x /usr/local/bin/picasso-dev /usr/local/bin/hermes-repatch-dev

echo "=== 检查 ==="
echo "dev .env 生效渠道行数（应为 0）: $(grep -cE '^(FEISHU_|WEIXIN_)' /home/dev/.hermes/.env || true)"
grep -E '^API_SERVER_(PORT|HOST)' /home/dev/.hermes/.env
grep 'baseURL' /opt/lc-dev/librechat.yaml
grep 'name:' /opt/lc-dev/librechat.yaml | head -2
ls -la /opt/lc-dev/
echo "✅ Dev LibreChat 栈就绪"
