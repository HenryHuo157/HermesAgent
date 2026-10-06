#!/usr/bin/env python3
"""Inject artifact-card styling into LibreChat's served index.html (in-container)."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'artifact-card-style-2026'

CSS = """
<style>
/* " + MARK + " : make artifact chip a prominent card with open button */
div:has(> button[data-artifact-trigger]){
  height:auto !important;
  margin:12px 0 !important;
  padding:14px 18px !important;
  border:1px solid rgba(120,120,140,.28);
  border-radius:14px;
  background:linear-gradient(135deg,rgba(99,102,241,.08),rgba(37,99,235,.04));
  box-shadow:0 1px 3px rgba(15,23,42,.06);
  transition:border-color .15s, box-shadow .15s;
}
div:has(> button[data-artifact-trigger]):hover{
  border-color:rgba(99,102,241,.6);
  box-shadow:0 4px 14px rgba(79,70,229,.15);
}
button[data-artifact-trigger]{
  width:100%;
  padding:2px 0;
  font-size:15px;
}
button[data-artifact-trigger]::after{
  content:'打开 ▸';
  margin-left:auto;
  padding:6px 16px;
  border-radius:999px;
  background:#4f46e5;
  color:#fff;
  font-size:13px;
  font-weight:600;
  white-space:nowrap;
}
</style>
"""

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# read current index.html from inside the container
r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read index.html from container: ' + r.stderr)
html = r.stdout

if MARK in html:
    print('[already styled]')
else:
    assert '</head>' in html, 'no </head> in index.html'
    html = html.replace('</head>', CSS + '\n</head>', 1)
    # write back through the container
    open('/tmp/lc_index_patched.html', 'w', encoding='utf-8').write(html)
    r2 = run('docker cp /tmp/lc_index_patched.html librechat-api:' + INDEX)
    if r2.returncode != 0:
        sys.exit('docker cp failed: ' + r2.stderr)
    r3 = run('docker exec librechat-api sh -c "chown node:node ' + INDEX + ' 2>/dev/null; true"')
    print('[style injected into index.html]')
print('[note] re-apply after container recreate: python3 /tmp/patch_artifact_card.py')
