#!/bin/bash
# fix-dev-paths.sh — 把 dev 副本里残留的 /home/admin 引用与生产交付路径全部改写为 dev 专属
# （Hermes 是 editable pip 安装，venv 的 finder/.pth/console-script 硬编码了安装时的绝对路径；
#   另含媒体交付管线：共享盘→-dev、绝对 /m/ 链接→相对，防止 Dev 把图发到生产域名）
set -u
n=0
while IFS= read -r f; do
  sed -i -e 's|/home/admin|/home/dev|g' \
         -e 's|/srv/hermes-share-dev|__DEVSHARE__|g' \
         -e 's|/srv/hermes-share|/srv/hermes-share-dev|g' \
         -e 's|__DEVSHARE__|/srv/hermes-share-dev|g' \
         -e 's|https://47.243.79.144/m/|/m/|g' "$f"
  n=$((n+1))
done < <(grep -rlI -e '/home/admin' -e '/srv/hermes-share' -e '47.243.79.144/m/' \
           /home/dev/.hermes/hermes-agent /home/dev/.hermes/bin /home/dev/.local/bin 2>/dev/null)
echo "改写 $n 个文件"
chown -R dev:dev /home/dev/.hermes /home/dev/.local
# 复查：dev 侧不应再有 admin 路径
left=$(grep -rlI '/home/admin' /home/dev/.hermes 2>/dev/null | wc -l)
echo "剩余引用 admin 路径的文件数: $left"
systemctl --user -M dev@.host restart hermes-gateway
echo "已重启 Dev 网关"
