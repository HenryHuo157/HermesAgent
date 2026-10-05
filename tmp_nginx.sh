#!/bin/bash
grep -n 'listen' /etc/nginx/conf.d/hermes-public.conf
echo '--- curl http test ---'
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' http://127.0.0.1/
