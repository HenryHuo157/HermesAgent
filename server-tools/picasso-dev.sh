#!/bin/bash
# picasso-dev — Dev 环境一站式控制（Dev Hermes 8643 + Dev LibreChat 3081，均只绑本机回环）
#
# 用法（root）：
#   picasso-dev start       # 拉起 Dev Hermes + Dev LibreChat（测试时段约 1.1G 内存）
#   picasso-dev stop        # 全部停止，释放内存
#   picasso-dev status      # 看两边状态
#   picasso-dev lc-restart  # 只重启 Dev LibreChat（改 UI 补丁后生效用）
#   picasso-dev repatch     # Dev Hermes 源码补丁重打（= hermes-repatch-dev）
#   picasso-dev skills      # 重新生成 Dev 技能索引并注入容器（改了 /home/dev/.hermes/skills 后）
#
# 对外不暴露：没有 nginx 条目、没有防火墙端口。本机访问：
#   LibreChat Dev  http://127.0.0.1:3081   （SSH 隧道：ssh -L 3081:127.0.0.1:3081 root@服务器）
#   Hermes Dev API http://127.0.0.1:8643   （同上 -L 8643:127.0.0.1:8643）
set -u
C=/opt/lc-dev/docker-compose.yml
UG="systemctl --user -M dev@.host"

case "${1:-status}" in
  start)
    echo "—— 启动 Dev Hermes（127.0.0.1:8643）——"
    $UG start hermes-gateway
    echo "—— 启动 Dev LibreChat（127.0.0.1:3081）——"
    docker compose -f "$C" up -d
    picasso-dev-skills || true
    sleep 2
    picasso-dev status
    echo "提示：Dev LibreChat 约 40 秒后就绪；隧道示例见脚本头部注释。" ;;
  stop)
    docker compose -f "$C" down 2>/dev/null
    $UG stop hermes-gateway 2>/dev/null
    $UG reset-failed hermes-gateway 2>/dev/null
    echo "—— Dev 环境已全部停止，内存释放 ——"
    free -h | head -2 ;;
  status)
    echo "Dev Hermes   : $($UG is-active hermes-gateway 2>&1)"
    echo "Dev LibreChat: $(docker ps --filter name=librechat-dev-api --format '{{.Status}}' || true)"
    echo "端口监听     : $(ss -tlnp 2>/dev/null | grep -E ':(3081|8643)\b' | awk '{print $4}' | tr '\n' ' ')"
    free -h | sed -n '2p' ;;
  lc-restart)
    docker restart librechat-dev-api >/dev/null && echo "Dev LibreChat 重启完成，约 40 秒后就绪" ;;
  repatch)
    /usr/local/bin/hermes-repatch-dev ;;
  skills)
    /usr/local/bin/picasso-dev-skills ;;
  *)
    echo "用法: picasso-dev start|stop|status|lc-restart|repatch|skills" ;;
esac
