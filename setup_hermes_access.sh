#!/bin/bash
# Set up secure public access for the Hermes Agent dashboard:
#  - dashboard.basic_auth (scrypt hash) appended to config.yaml
#  - start-webui.sh rebound to 0.0.0.0 so the auth gate engages
#  - self-signed TLS + reverse proxy on 443, port 80 redirects to https
set -e

IP=47.243.79.144
CONF=/home/admin/.hermes/config.yaml

# --- 1. generate secrets (on server, never leave it in plaintext files) ---
PW=$(tr -dc 'A-HJ-NP-Za-km-z2-9' </dev/urandom | head -c 20)
SECRET=$(openssl rand -base64 32)
HASH=$(cd /home/admin/.hermes/hermes-agent && HPC_PW="$PW" ./venv/bin/python -c \
  "import sys,os; sys.path.insert(0,'.'); from plugins.dashboard_auth.basic import hash_password; print(hash_password(os.environ['HPC_PW']))")

# --- 2. append basic_auth block to config.yaml ---
if grep -q '^dashboard:' "$CONF"; then
  echo "ERROR: an active 'dashboard:' key already exists in config.yaml — manual merge needed"
  exit 1
fi
cp "$CONF" "$CONF.bak.$(date +%Y%m%d_%H%M%S)"
cat >> "$CONF" <<EOF

# ==== Team web access (added $(date +%F)) ====
dashboard:
  basic_auth:
    username: "admin"
    password_hash: "$HASH"
    secret: "$SECRET"
EOF
chown admin:admin "$CONF"
echo "[ok] config.yaml updated (backup saved)"

# --- 3. rebind dashboard to 0.0.0.0 so auth gate engages ---
sed -i 's/--host 127\.0\.0\.1/--host 0.0.0.0/' /home/admin/.hermes/bin/start-webui.sh
grep -- --host /home/admin/.hermes/bin/start-webui.sh
echo "[ok] start-webui.sh rebound to 0.0.0.0"

# --- 4. self-signed cert ---
mkdir -p /etc/nginx/ssl
openssl req -x509 -newkey rsa:2048 -nodes -days 825 \
  -keyout /etc/nginx/ssl/hermes.key -out /etc/nginx/ssl/hermes.crt \
  -subj "/CN=hermes-aliyun" -addext "subjectAltName=IP:$IP" 2>/dev/null
chmod 600 /etc/nginx/ssl/hermes.key
echo "[ok] self-signed cert created"

# --- 5. nginx public vhost (reuses the connection_upgrade map from hermes-internal.conf) ---
cat > /etc/nginx/conf.d/hermes-public.conf <<'EOF'
server {
    listen 80;
    server_name 47.243.79.144;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl default_server;
    server_name 47.243.79.144;

    ssl_certificate     /etc/nginx/ssl/hermes.crt;
    ssl_certificate_key /etc/nginx/ssl/hermes.key;

    client_max_body_size 100m;

    location / {
        proxy_pass http://127.0.0.1:9120;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP $remote_addr;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
}
EOF
nginx -t
echo "[ok] nginx vhost written"

# --- 6. restart services ---
systemctl reload nginx
sudo -u admin XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart hermes-webui
sleep 5
systemctl is-active nginx
sudo -u admin XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active hermes-webui

# --- 7. verify auth gate engaged ---
echo "--- /api/status ---"
curl -s -m 10 http://127.0.0.1:9120/api/status | head -c 600
echo
echo "=== CREDENTIALS ==="
echo "USERNAME=admin"
echo "PASSWORD=$PW"
