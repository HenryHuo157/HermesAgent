#!/usr/bin/env python3
"""Dump the Hermes skill index (name + description) to a JSON for the web picker."""
import glob, json, os, re

SKILLS_DIR = '/home/admin/.hermes/skills'
OUT = '/srv/hermes-share/skills.json'

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
        # 取第一个非标题段落行兜底
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith('#') and not s.startswith('---'):
                desc = s[:80]
                break
    return name, (desc or '')

def main():
    skills = []
    for path in sorted(glob.glob(SKILLS_DIR + '/*/*/SKILL.md')):
        rel = os.path.relpath(os.path.dirname(path), SKILLS_DIR)
        name, desc = parse_frontmatter(path)
        skills.append({
            'name': name or rel.replace('/', '-'),
            'desc': desc or '',
            'path': rel,
        })
    tmp = OUT + '.tmp'
    json.dump({'updated': __import__('time').strftime('%Y-%m-%d %H:%M'), 'skills': skills},
              open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    print('skills.json:', len(skills), 'skills')

main()
