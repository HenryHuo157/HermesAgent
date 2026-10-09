#!/bin/bash
# pwpanel Dev 端到端验证（yoyoli 账号临时改密后改回）
echo "=== 1. pwpanel 进程存活"
pgrep -f 'pwpanel-dev/app[.]py --dev' >/dev/null && echo "pwpanel running" || { echo "pwpanel NOT running"; exit 1; }

echo "=== 2. 经 nginx3082 /pw/ 改密码 (yoyoli: HB3tPEKqytzH -> DevTest12345)"
curl -s -X POST http://127.0.0.1:3082/pw/api/change -H 'Content-Type: application/json' \
  -d '{"email":"yoyoli@mainplan.com.hk","currentPassword":"HB3tPEKqytzH","newPassword":"DevTest12345"}'; echo

echo "=== 3. 旧密码登录（预期失败 401）"
code=$(curl -s -o /tmp/old.json -w '%{http_code}' -X POST http://127.0.0.1:3081/api/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"yoyoli@mainplan.com.hk","password":"HB3tPEKqytzH"}')
echo "http=$code body=$(head -c 160 /tmp/old.json)"

echo "=== 4. 新密码登录（预期 200 + token）"
code=$(curl -s -o /tmp/new.json -w '%{http_code}' -X POST http://127.0.0.1:3081/api/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"yoyoli@mainplan.com.hk","password":"DevTest12345"}')
echo "http=$code body=$(head -c 80 /tmp/new.json)"

echo "=== 5. 再改回初始密码 (DevTest12345 -> HB3tPEKqytzH)（反向流程复验）"
curl -s -X POST http://127.0.0.1:3082/pw/api/change -H 'Content-Type: application/json' \
  -d '{"email":"yoyoli@mainplan.com.hk","currentPassword":"DevTest12345","newPassword":"HB3tPEKqytzH"}'; echo

echo "=== 6. 错误的当前密码（预期 error:current，不泄露账号存在性）"
curl -s -X POST http://127.0.0.1:3082/pw/api/change -H 'Content-Type: application/json' \
  -d '{"email":"nobody-check@mainplan.com.hk","currentPassword":"WRONGpass999","newPassword":"Whatever123"}'; echo

echo "=== 7. 过短新密码（预期 error:invalid）"
curl -s -X POST http://127.0.0.1:3082/pw/api/change -H 'Content-Type: application/json' \
  -d '{"email":"yoyoli@mainplan.com.hk","currentPassword":"HB3tPEKqytzH","newPassword":"short"}'; echo

echo "=== 8. 初始密码恢复确认（重新用 HB3tPEKqytzH 登录，预期 200）"
code=$(curl -s -o /tmp/final.json -w '%{http_code}' -X POST http://127.0.0.1:3081/api/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"yoyoli@mainplan.com.hk","password":"HB3tPEKqytzH"}')
echo "http=$code"
