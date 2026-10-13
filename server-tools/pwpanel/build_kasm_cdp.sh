#!/bin/bash
set -e
# 构建带 CDP 调试端口的 Kasm Chrome 沙盒镜像(持久化参数注入)
cat > /tmp/sandbox-build/Dockerfile.kasm <<'EOF'
FROM kasmweb/chrome:1.16.1
USER root
RUN sed -i 's|/opt/google/chrome/google-chrome --password-store=basic|/opt/google/chrome/google-chrome --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --password-store=basic|g' /usr/bin/google-chrome \
    && grep -c 'remote-debugging-port=9222' /usr/bin/google-chrome
EOF
docker build -t picasso-browser:latest -f /tmp/sandbox-build/Dockerfile.kasm /tmp/sandbox-build/ 2>&1 | tail -2
docker rm -f picasso-browser 2>/dev/null || true
docker run -d --name picasso-browser --shm-size=512m -p 6901:6901 -p 9222:9222 picasso-browser:latest
sleep 8
docker exec picasso-browser sh -c 'curl -s -m 3 http://127.0.0.1:9222/json/version 2>/dev/null | head -c 150 || ps aux | grep -i [c]hrome | head -1 | cut -c1-150'
echo
curl -s -m 5 http://127.0.0.1:9222/json/version | head -c 150; echo " <- host 9222"
