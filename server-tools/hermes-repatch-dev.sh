#!/bin/bash
# hermes-repatch-dev — Dev Hermes 源码补丁重打（先在 dev 上验证补丁，再上生产）
#
# 用法（root）：
#   hermes-repatch-dev --sync   # 从 /opt/hermes-patches（生产补丁库）重新派生 dev 补丁库后执行
#   hermes-repatch-dev          # 直接用现有 /opt/hermes-patches-dev 执行
#
# 与生产版 hermes-repatch 的区别：
#   - 补丁库 /opt/hermes-patches-dev/（由生产库 sed 替换 /home/admin→/home/dev 派生）
#   - 目标安装 /home/dev/.hermes/hermes-agent
#   - 变更后重启的是 dev 网关（生产不受影响）
set -u
D=/opt/hermes-patches-dev
HER=/home/dev/.local/bin/hermes
AG=/home/dev/.hermes/hermes-agent
API=$AG/gateway/platforms/api_server.py
changed=0

if [ "${1:-}" = "--sync" ]; then
  echo "—— 从生产补丁库派生 dev 补丁库 ——"
  mkdir -p "$D"
  for f in /opt/hermes-patches/patch_*.py; do
    # 路径派生：admin→dev；共享盘→-dev（占位符防二次后缀）；媒体链接改相对（生产443/Dev3082 各自同源）
    sed -e 's|/home/admin|/home/dev|g' \
        -e 's|/srv/hermes-share-dev|__DEVSHARE__|g' \
        -e 's|/srv/hermes-share|/srv/hermes-share-dev|g' \
        -e 's|__DEVSHARE__|/srv/hermes-share-dev|g' \
        -e 's|https://47.243.79.144/m/|/m/|g' "$f" > "$D/$(basename "$f")"
  done
fi

if [ ! -d "$AG" ]; then
  echo "❌ Dev Hermes 未安装：先跑 build-dev-hermes.sh"; exit 1
fi

step() {
  local before after
  sleep 1
  before=$(stat -c %Y "$API" "$AG/cron/lifecycle_guard.py" "$AG/tools/terminal_tool.py" 2>/dev/null | md5sum)
  echo "== $1"
  python3 "$D/$1" || { echo "❌ $1 失败——上游代码结构可能变了，已停止（用文件旁最新 .bak 回滚）"; exit 1; }
  after=$(stat -c %Y "$API" "$AG/cron/lifecycle_guard.py" "$AG/tools/terminal_tool.py" 2>/dev/null | md5sum)
  [ "$before" != "$after" ] && changed=1
  return 0
}

echo "—— Dev Hermes 源码补丁检查/重打 ——"
grep -q PATCH-NUL-2026 "$AG/tools/terminal_tool.py" || step patch_null_bytes.py
grep -q PATCH-NUL-V2 "$AG/cron/lifecycle_guard.py" || step patch_null_v2.py
grep -q PATCH-REASONING-2026 "$API" || step patch_reasoning_param.py

if grep -q _v8short "$API"; then
  echo "== 活动时间线已是 v8 —— 跳过整条链条"
elif grep -q PATCH-THINK-V6 "$API"; then
  step patch_green_check_v2.py
  step patch_think_v8.py
elif grep -q PATCH-ACTIVITY-2026 "$API"; then
  step patch_media_v4.py
  step patch_media_v5.py
  step patch_think_v6.py
  step patch_green_check_v2.py
  step patch_think_v8.py
else
  step patch_activity_v3.py
  step patch_media_v4.py
  step patch_media_v5.py
  step patch_think_v6.py
  step patch_green_check_v2.py
  step patch_think_v8.py
fi

step patch_fp_2026.py

echo "—— 语法校验 ——"
for f in "$API" "$AG/cron/lifecycle_guard.py" "$AG/tools/terminal_tool.py"; do
  python3 -c "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$f" \
    || { echo "❌ $f 语法错误！用旁边最新 .bak 恢复"; exit 1; }
done
echo "语法 OK"

if [ "$changed" = 1 ]; then
  echo "—— 检测到新补丁，重启 Dev 网关 ——"
  sudo -u dev -H "$HER" gateway restart
else
  echo "—— 无变更，不重启 ——"
fi
echo "✅ hermes-repatch-dev 完成（生产未受影响）"
