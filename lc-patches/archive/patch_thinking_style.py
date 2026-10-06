#!/usr/bin/env python3
"""Inject muted/compact styling for LibreChat reasoning (思考過程) blocks."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'thinking-thin-2026'

CSS = """<style>
/* PATCH-MARK: thinking-thin-2026 — Claude/Codex 风格：思考块小字、浅灰、低调 */
.group\\/reasoning, .group\\/reasoning-compact{
  font-size:12.5px !important;
  color:#8b93a5 !important;
}
.group\\/reasoning p,
.group\\/reasoning span,
.group\\/reasoning div,
.group\\/reasoning li,
.group\\/reasoning blockquote{
  font-size:12.5px !important;
  color:#8b93a5 !important;
  line-height:1.55;
}
.group\\/reasoning pre,
.group\\/reasoning code,
.group\\/reasoning pre *{
  font-size:11px !important;
  color:#8b93a5 !important;
  background:rgba(130,140,160,.06) !important;
}
.group\\/reasoning .overflow-hidden{
  background:rgba(130,140,160,.05) !important;
  padding:8px 12px !important;
}
.group\\/thinking-container > div:first-child{
  margin:2px 0 !important;
  padding:2px 0 !important;
}
.group\\/reasoning-compact{ margin:4px 0 !important; }
</style>
"""

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read index.html: ' + r.stderr)
html = r.stdout

if MARK in html:
    print('[thinking-thin style already present]')
else:
    assert '</head>' in html, 'no </head>'
    html = html.replace('</head>', CSS + '\n</head>', 1)
    open('/tmp/lc_index_v2.html', 'w', encoding='utf-8').write(html)
    r2 = run('docker cp /tmp/lc_index_v2.html librechat-api:' + INDEX)
    if r2.returncode != 0:
        sys.exit('docker cp failed: ' + r2.stderr)
    print('[thinking-thin style injected]')
