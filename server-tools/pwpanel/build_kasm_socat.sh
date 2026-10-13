#!/bin/bash
set -e
# 第二层镜像:桥接模式下打通宿主->容器 CDP
# chrome 只接受本机来源的调试连接(docker-proxy 转发会被 reset),
# 用容器内 socat(127.0.0.1:9223 -> 127.0.0.1:9222)中转,宿主经 -p 9223 访问。
cat > /tmp/sandbox-build/Dockerfile.socat <<'EOF'
FROM picasso-browser:latest
USER root
RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/* \
    && printf '#!/bin/bash\nsocat TCP-LISTEN:9223,bind=127.0.0.1,fork,reuseaddr TCP:127.0.0.1:9222 &\nwhile true; do sleep 3600; done\n' > /dockerstartup/custom_startup.sh \
    && chmod +x /dockerstartup/custom_startup.sh
EOF
docker build -t picasso-browser:latest -f /tmp/sandbox-build/Dockerfile.socat /tmp/sandbox-build/ 2>&1 | tail -2
docker rm -f picasso-browser 2>/dev/null || true
docker run -d --name picasso-browser --shm-size=512m -p 6901:6901 -p 9223:9223 picasso-browser:latest
sleep 10
echo "=== host -> 9223 (socat -> chrome CDP) ==="
curl -s -m 5 http://127.0.0.1:9223/json/version | head -c 120; echo
echo "=== kasm web 6901 ==="
curl -s -o /dev/null -w '%{http_code}\n' -m 5 http://127.0.0.1:6901/
