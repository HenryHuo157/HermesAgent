#!/usr/bin/env python3
"""Hide the agent capability badge chips (fake toggles) above the composer."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'hide-badges-2026'

CSS = """<style>
/* PATCH-MARK: hide-badges-2026 — 隐藏对 Hermes 无效的工具芯片行 */
.relative.flex.flex-wrap.items-center.gap-2:has(> .badge-icon){ display:none !important; }
</style>
"""

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read index.html: ' + r.stderr)
html = r.stdout

if MARK in html:
    print('[hide-badges already present]')
else:
    assert '</head>' in html, 'no </head>'
    html = html.replace('</head>', CSS + '\n</head>', 1)
    open('/tmp/lc_index_hidebadges.html', 'w', encoding='utf-8').write(html)
    r2 = run('docker cp /tmp/lc_index_hidebadges.html librechat-api:' + INDEX)
    if r2.returncode != 0:
        sys.exit('docker cp failed: ' + r2.stderr)
    print('[hide-badges injected]')
