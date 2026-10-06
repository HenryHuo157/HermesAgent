#!/bin/bash
# build-dev-hermes.sh — 一次性搭建 Dev Hermes（root 执行）
# 产出：dev 用户 + /home/dev/.hermes 独立副本（端口 8643、渠道禁用、输出目录隔离）
# 幂等：重复执行只补缺的文件，不覆盖已有定制。真实安装参数见 部署清单.md「Live/Dev 双环境」。
set -euo pipefail

ADM=/home/admin/.hermes
DEV=/home/dev/.hermes

if ! id dev &>/dev/null; then
  useradd -m -s /bin/bash dev
  passwd -l dev                      # 无密码，仅 root 可 su/sudo -u
  loginctl enable-linger dev         # 用户管理器常驻（服务可被 root 按需启停）；单元不 enable，重启不自动拉起
fi

mkdir -p "$DEV" /home/dev/.local/bin /home/dev/.config/systemd/user /srv/hermes-share-dev
chown dev:dev /srv/hermes-share-dev

# —— 程序体与运行资产（大件，存在即跳过）——
[ -d "$DEV/hermes-agent" ] || cp -a "$ADM/hermes-agent" "$DEV/hermes-agent"
[ -d "$DEV/bin" ]  || cp -a "$ADM/bin"  "$DEV/bin"
[ -d "$DEV/skills" ] || cp -a "$ADM/skills" "$DEV/skills"
[ -d "$DEV/plugins" ] || cp -a "$ADM/plugins" "$DEV/plugins"
# —— 配置（每次同步，跟生产保持一致为基线）——
cp -a "$ADM/config.yaml" "$DEV/config.yaml"
cp -a "$ADM/SOUL.md"     "$DEV/SOUL.md"
cp -a "$ADM/.env"        "$DEV/.env"
[ -f "$ADM/auth.json" ] && cp -a "$ADM/auth.json" "$DEV/auth.json"
cp -a "$ADM/models_dev_cache.json" "$DEV/models_dev_cache.json" 2>/dev/null || true
# 注意：刻意不复制 state.db / cron/ / sessions/ / memories/ / weixin/ / kanban.db 等
# —— 否则生产定时任务（早报等）会在 dev 里重复触发。

# —— hermes 启动器（指向 dev 路径）——
sed 's|/home/admin|/home/dev|g' /home/admin/.local/bin/hermes > /home/dev/.local/bin/hermes
chmod +x /home/dev/.local/bin/hermes

# —— SOUL 输出目录隔离：dev 的文件交付落到 /srv/hermes-share-dev，不污染用户可见的共享盘 ——
sed -i 's|/srv/hermes-share|/srv/hermes-share-dev|g' "$DEV/SOUL.md"

# —— .env：渠道必须留在生产（同一飞书 app 双连接会抢消息）；API 改 8643 ——
# HOST 绑 0.0.0.0（Dev LibreChat 容器经 docker 网桥访问需要；8643 不在阿里云防火墙放行列表，外网不可达）
python3 - <<'EOF'
import os
p = '/home/dev/.hermes/.env'
lines = open(p).read().splitlines()
out = []
for l in lines:
    if l.startswith(('FEISHU_', 'WEIXIN_')) and not l.startswith('#'):
        out.append('# DEV-DISABLED（渠道只许生产实例连接，防抢消息） ' + l)
    elif l.startswith(('API_SERVER_HOST=', 'API_SERVER_PORT=')):
        continue  # 原有 HOST/PORT 行删除，统一由下方 Dev 块声明
    else:
        out.append(l)
out += ['', '# —— Dev 专属（build-dev-hermes.sh 写入，勿删）——',
        'API_SERVER_PORT=8643',
        'API_SERVER_HOST=0.0.0.0']
open(p, 'w').write('\n'.join(out) + '\n')
os.chmod(p, 0o600)
EOF

# —— systemd 用户单元（照抄生产的，改路径；不 enable = 重启不自动跑）——
sed 's|/home/admin|/home/dev|g' /home/admin/.config/systemd/user/hermes-gateway.service \
  > /home/dev/.config/systemd/user/hermes-gateway.service

chown -R dev:dev /home/dev/.hermes /home/dev/.local /home/dev/.config

systemctl --user -M dev@.host daemon-reload || echo "（user manager 尚未就绪，daemon-reload 跳过——首次 start 前会重试）"

echo "✅ Dev Hermes 就绪：dev 用户 / 8643 端口 / 渠道已禁 / 输出走 /srv/hermes-share-dev"
echo "   启停用 picasso-dev start|stop（尚未启动）"
