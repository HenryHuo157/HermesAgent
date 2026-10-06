#!/bin/bash
# fix-dev-paths.sh — 把 dev 副本里残留的 /home/admin 引用全部改写为 /home/dev
# （Hermes 是 editable pip 安装，venv 的 finder/.pth/console-script 硬编码了安装时的绝对路径）
set -u
n=0
while IFS= read -r f; do
  sed -i 's|/home/admin|/home/dev|g' "$f"
  n=$((n+1))
done < <(grep -rlI '/home/admin' /home/dev/.hermes/hermes-agent /home/dev/.hermes/bin /home/dev/.local/bin 2>/dev/null)
echo "改写 $n 个文件"
chown -R dev:dev /home/dev/.hermes /home/dev/.local
# 复查：dev 侧不应再有 admin 路径
left=$(grep -rlI '/home/admin' /home/dev/.hermes 2>/dev/null | wc -l)
echo "剩余引用 admin 路径的文件数: $left"
systemctl --user -M dev@.host restart hermes-gateway
echo "已重启 Dev 网关"
