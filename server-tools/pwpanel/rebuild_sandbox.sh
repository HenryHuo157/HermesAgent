#!/bin/bash
set -e
# 第三层镜像:socat 本机转发(chrome 只接受本机来源的调试连接),
# custom_startup 只做后台启动后立即退出——阻塞会挡住 Kasm 后续的 chrome 启动
cat > /tmp/sandbox-build/Dockerfile.socat <<'EOF'
FROM picasso-browser:latest
USER root
RUN apt-get update; apt-get install -y --no-install-recommends socat; rm -rf /var/lib/apt/lists/*
RUN printf '#!/bin/bash\nnohup socat TCP-LISTEN:9223,bind=127.0.0.1,fork,reuseaddr TCP:127.0.0.1:9222 >/dev/null 2>&1 &\n' > /dockerstartup/custom_startup.sh \
    && chmod +x /dockerstartup/custom_startup.sh
EOF
docker build -q -t picasso-browser:latest -f /tmp/sandbox-build/Dockerfile.socat /tmp/sandbox-build/
docker rm -f picasso-browser 2>/dev/null || true
docker run -d --name picasso-browser --shm-size=512m -p 6901:6901 -p 9223:9223 picasso-browser:latest
sleep 14
echo "=== 9223 (socat->chrome CDP) ==="
curl -s -m 5 http://127.0.0.1:9223/json/version | head -c 130
echo
echo "=== chrome process count ==="
docker exec picasso-browser sh -c 'ps aux | grep -c [c]hrome'
echo "=== 6901 kasm web ==="
curl -s -o /dev/null -w '%{http_code}\n' -m 5 http://127.0.0.1:6901/
