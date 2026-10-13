#!/bin/bash
set -e
# 自定义沙盒镜像:nikolaik 基础(python+node+git) + GitHub CLI
mkdir -p /tmp/sandbox-build
cat > /tmp/sandbox-build/Dockerfile <<'EOF'
FROM nikolaik/python-nodejs:python3.11-nodejs20
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && GH_VER=2.63.2 \
    && curl -sL "https://github.com/cli/cli/releases/download/v${GH_VER}/gh_${GH_VER}_linux_amd64.tar.gz" \
       | tar xz -C /tmp \
    && install /tmp/gh_${GH_VER}_linux_amd64/bin/gh /usr/local/bin/gh \
    && rm -rf /tmp/gh_${GH_VER}_linux_amd64 /var/lib/apt/lists/* \
    && gh --version
EOF
cat > /tmp/sandbox-build/build.sh <<'EOF'
#!/bin/bash
docker build -t hermes-sandbox:latest /tmp/sandbox-build/
EOF
chmod +x /tmp/sandbox-build/build.sh
bash /tmp/sandbox-build/build.sh 2>&1 | tail -4
