#!/bin/bash
# hermes-repatch — Hermes 源码补丁一键检查/重打（升级 Hermes 后 root 跑一次）
# 补丁库：/opt/hermes-patches/（与本机仓库 Hermes Agents/patch_*.py 保持一致）
# 链条：null→null_v2→[activity_v3→media_v4→v5→think_v6→green_check_v2→think_v8]→reasoning→fp2026
# 各脚本自带幂等检查（重复跑安全）；任一步失败立即停止，用目标文件旁最新 .bak 可回滚。
# 有实际变更时自动 `hermes gateway restart`；无变更不动线上。
set -u
D=/opt/hermes-patches
HER=/home/admin/.local/bin/hermes
AG=/home/admin/.hermes/hermes-agent
API=$AG/gateway/platforms/api_server.py
changed=0

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

echo "—— Hermes 源码补丁检查/重打 ——"
grep -q PATCH-NUL-2026 "$AG/tools/terminal_tool.py" || step patch_null_bytes.py
grep -q PATCH-NUL-V2 "$AG/cron/lifecycle_guard.py" || step patch_null_v2.py
grep -q PATCH-REASONING-2026 "$API" || step patch_reasoning_param.py

# —— 活动时间线链条（v8 为终点；_v8short 是 v8 实况指纹，v8 后标记会被重命名逻辑吞掉）——
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

# —— FP-2026 会话指纹三元组（幂等）——
step patch_fp_2026.py

echo "—— 语法校验 ——"
for f in "$API" "$AG/cron/lifecycle_guard.py" "$AG/tools/terminal_tool.py"; do
  python3 -c "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$f" \
    || { echo "❌ $f 语法错误！用旁边最新 .bak 恢复"; exit 1; }
done
echo "语法 OK"

if [ "$changed" = 1 ]; then
  echo "—— 检测到新补丁，重启网关 ——"
  sudo -u admin -H "$HER" gateway restart
else
  echo "—— 无变更，不重启 ——"
fi
echo "✅ hermes-repatch 完成"
