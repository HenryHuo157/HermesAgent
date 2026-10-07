#!/bin/bash
# picasso-dev-skills — 生成 Dev 技能索引并注入 Dev LibreChat 容器（幂等，可随时重跑）
#
# 背景：技能选择器在生产走 /m/skills.json（nginx → /srv/hermes-share/skills.json），
#       Dev 走 SSH 隧道不经过 nginx，所以把 Dev 自己的技能索引（/home/dev/.hermes/skills）
#       生成后 docker cp 进容器 dist（/skills.json，免认证静态、同源）。
# 选择器读法：先 /skills.json（Dev 命中）→ 失败回退 /m/skills.json（生产命中）。
#
# 何时重跑：改了 Dev 技能（/home/dev/.hermes/skills）之后；
#           picasso-dev start 和 deploy_lc_patches.py --dev 都会自动调用。
set -euo pipefail

OUT=/opt/lc-dev/skills.json
SKILLS_DIR=/home/dev/.hermes/skills

if [ ! -d "$SKILLS_DIR" ]; then
  echo "❌ $SKILLS_DIR 不存在——Dev Hermes 未安装？"; exit 1
fi

python3 - "$SKILLS_DIR" "$OUT" <<'EOF'
import glob, json, os, re, sys, time

SKILLS_DIR, OUT = sys.argv[1], sys.argv[2]

def parse_frontmatter(path):
    try:
        text = open(path, encoding='utf-8').read()
    except Exception:
        return None, None
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    name = desc = None
    if m:
        for line in m.group(1).splitlines():
            lm = re.match(r'^name:\s*"?([^"\n]+)"?\s*$', line.strip())
            ld = re.match(r'^description:\s*"?(.*?)"?\s*$', line.strip())
            if lm and not name:
                name = lm.group(1).strip()
            if ld and not desc:
                desc = ld.group(1).strip()
    if not name:
        name = os.path.basename(os.path.dirname(path))
    if not desc:
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith('#') and not s.startswith('---'):
                desc = s[:80]
                break
    return name, (desc or '')

skills = []
for path in sorted(glob.glob(SKILLS_DIR + '/*/*/SKILL.md')):
    rel = os.path.relpath(os.path.dirname(path), SKILLS_DIR)
    name, desc = parse_frontmatter(path)
    skills.append({'name': name or rel.replace('/', '-'), 'desc': desc or '', 'path': rel})

tmp = OUT + '.tmp'
json.dump({'updated': time.strftime('%Y-%m-%d %H:%M'), 'skills': skills},
          open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
os.replace(tmp, OUT)
print('generated:', len(skills), 'skills ->', OUT)
EOF

if docker ps --format '{{.Names}}' | grep -q '^librechat-dev-api$'; then
  docker cp "$OUT" librechat-dev-api:/app/client/dist/skills.json
  echo "injected into librechat-dev-api:/app/client/dist/skills.json"
else
  echo "（Dev 容器未运行——下次 picasso-dev start 时会自动注入）"
fi
