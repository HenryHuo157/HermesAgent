#!/bin/bash
# 畢卡索 每日备份（2026-10-06 重建；上次备份任务在 9-25 后丢失）
# 内容：LibreChat mongo + Hermes 配置/技能/会话库 + 服务器关键配置 + 共享盘 rsync 快照
# 保留：全部 7 天滚动。异地：mongo/hermes/configs 经 Syncthing 文件夹 picasso-backups
#       单向同步到 NAS（服务器 sendonly，share/ 快照不异地，见部署清单「备份与恢复」）
# cron（root）：30 3 * * * /usr/local/bin/picasso-backup >> /opt/backups/backup.log 2>&1
set -u
B=/opt/backups
D=$(date +%F)
rc=0
mkdir -p "$B/mongo" "$B/hermes" "$B/configs" "$B/share"
chmod 700 "$B"

log() { echo "[$(date '+%F %T')] $*"; }

# 1) LibreChat mongo（全部用户/会话/消息）
if docker exec librechat-mongo mongodump --archive --gzip > "$B/mongo/librechat-$D.archive.gz" 2>/dev/null; then
  log "mongo ok $(du -h "$B/mongo/librechat-$D.archive.gz" | cut -f1)"
else
  rc=1; log "mongo FAIL"
fi

# 2) Hermes：配置/SOUL/技能/.env/状态库（排除可重装本体与缓存）
if tar czf "$B/hermes/hermes-$D.tgz" -C /home/admin \
     --exclude='.hermes/hermes-agent' --exclude='.hermes/bin' \
     --exclude='.hermes/cache' --exclude='.hermes/logs' \
     --exclude='.hermes/audio_cache' --exclude='*.bak*' \
     .hermes 2>/dev/null; then
  log "hermes ok $(du -h "$B/hermes/hermes-$D.tgz" | cut -f1)"
else
  rc=1; log "hermes FAIL"
fi

# 3) 服务器关键配置：compose/LibreChat/补丁库/两个面板/SearXNG/nginx+ssl/crontab
if tar czf "$B/configs/server-$D.tgz" --ignore-failed-read \
     /opt/lc-run/docker-compose.yml /opt/lc-run/.env \
     /opt/librechat/librechat.yaml /opt/lc-patches \
     /opt/taskspanel /opt/usagepanel /opt/searxng/settings.yml \
     /opt/hermes-patches /etc/nginx/conf.d /etc/nginx/ssl \
     /var/spool/cron 2>/dev/null; then
  log "configs ok $(du -h "$B/configs/server-$D.tgz" | cut -f1)"
else
  rc=1; log "configs FAIL"
fi

# 4) 共享盘硬链接快照（每天只占增量空间）
last=$(ls -dt "$B"/share/snap-* 2>/dev/null | head -1)
if [ -n "$last" ]; then
  rsync -a --delete --link-dest="$last" /srv/hermes-share/ "$B/share/snap-$D/" || rc=1
else
  rsync -a /srv/hermes-share/ "$B/share/snap-$D/" || rc=1
fi
log "share snap-$D done $(du -sh "$B/share/snap-$D" 2>/dev/null | cut -f1)"

# 5) 7 天滚动清理
find "$B/mongo" "$B/hermes" "$B/configs" -type f -mtime +7 -delete 2>/dev/null
ls -dt "$B"/share/snap-* 2>/dev/null | tail -n +8 | xargs -r rm -rf

# 6) 属主给 syncthing 容器（PUID=1000）读取，供异地同步
chown -R 1000:1000 "$B" 2>/dev/null

# 7) 心跳（监控脚本据此判断备份新鲜度）
date +%s > "$B/last-backup.stamp"
chown 1000:1000 "$B/last-backup.stamp" 2>/dev/null
log "done rc=$rc"
exit $rc
