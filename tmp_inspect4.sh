#!/bin/bash
docker exec librechat-api sh -c "grep -o '.\{3500\}com_ui_thinking.\{4500\}' /app/client/dist/assets/hooks.BALLZO6i.js" > /tmp/reasoning_ctx.txt 2>/dev/null
wc -c /tmp/reasoning_ctx.txt
cat /tmp/reasoning_ctx.txt
