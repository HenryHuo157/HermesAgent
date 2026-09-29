#!/bin/bash
# Deploy the simple team chat front-end:
#  /       -> static Chinese chat page (nginx basic auth, user "team")
#  /api/   -> proxied to hermes API server 8642 with server-side key injection
#  /files/ -> shared deliverables dir (autoindex)
#  /admin  -> original hermes dashboard (unchanged auth)
set -e
IP=47.243.79.144
APIKEY=$(grep '^API_SERVER_KEY=' /home/admin/.hermes/.env | cut -d= -f2)

# --- 1. dirs ---
mkdir -p /var/www/chat /srv/hermes-share
chown admin:admin /srv/hermes-share
chmod 755 /srv/hermes-share
echo "欢迎～ AI 生成的文件都会放在这里" > /srv/hermes-share/读我.txt
chown admin:admin /srv/hermes-share/读我.txt
echo "[ok] dirs ready"

# --- 2. team account (nginx basic auth) ---
PW=$(tr -dc 'A-HJ-NP-Za-km-z2-9' </dev/urandom | head -c 16)
printf 'team:%s\n' "$(openssl passwd -apr1 "$PW")" > /etc/nginx/.htpasswd_chat
chmod 640 /etc/nginx/.htpasswd_chat
echo "[ok] htpasswd created"

# --- 3. nginx vhost ---
cat > /etc/nginx/conf.d/hermes-public.conf <<EOF
server {
    listen 80;
    server_name $IP;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl default_server;
    server_name $IP;

    ssl_certificate     /etc/nginx/ssl/hermes.crt;
    ssl_certificate_key /etc/nginx/ssl/hermes.key;

    client_max_body_size 100m;

    # ---- 同事聊天页 ----
    location / {
        root /var/www/chat;
        index index.html;
        auth_basic "TeamAI";
        auth_basic_user_file /etc/nginx/.htpasswd_chat;
        try_files \$uri \$uri/ /index.html;
    }

    # ---- API 代理（密钥只存在服务端）----
    location /api/ {
        auth_basic "TeamAI";
        auth_basic_user_file /etc/nginx/.htpasswd_chat;
        proxy_pass http://127.0.0.1:8642/v1/;
        proxy_set_header Authorization "Bearer $APIKEY";
        proxy_set_header Host \$host;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        gzip off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        chunked_transfer_encoding on;
    }

    # ---- 交付文件下载 ----
    location /files/ {
        auth_basic "TeamAI";
        auth_basic_user_file /etc/nginx/.htpasswd_chat;
        alias /srv/hermes-share/;
        autoindex on;
        autoindex_localtime on;
        add_header Cache-Control "no-store";
    }

    # ---- 管理后台（仅管理员）----
    location /admin {
        proxy_pass http://127.0.0.1:9120;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Prefix /admin;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
}
EOF
nginx -t
systemctl reload nginx
echo "[ok] nginx reloaded"

# --- 4. dashboard public_url for /admin prefix ---
CONF=/home/admin/.hermes/config.yaml
if ! grep -q '^  public_url:' "$CONF"; then
  sed -i '/^dashboard:/a\  public_url: "https://'"$IP"'/admin"' "$CONF"
  chown admin:admin "$CONF"
  sudo -u admin XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart hermes-webui
  sleep 4
fi
sudo -u admin XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active hermes-webui
echo "[ok] dashboard restarted with /admin prefix"

echo "=== TEAM CREDENTIALS ==="
echo "USERNAME=team"
echo "PASSWORD=$PW"
