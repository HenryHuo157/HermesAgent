#!/usr/bin/env python3
"""v5: move skill button to sit right after the settings (⚙️) button (host-side, docker cp)."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read index.html: ' + r.stderr)
html = r.stdout

if "anchor.parentElement.insertBefore(b, anchor.nextSibling)" in html:
    print('[v5 already applied]')
    sys.exit(0)

old1 = "    if(mine || !btns.length) return;\n    var send=btns[btns.length-1];           /* 发送键（最右） */\n    var b=document.createElement('button');\n    b.type='button'; b.id='lc-skillbtn'; b.innerHTML='🧩 技能';\n    b.addEventListener('click',function(e){ e.stopPropagation(); toggle(ta); });\n    send.parentElement.insertBefore(b, send);"
new1 = """    var anchor=btns[1]||btns[0];            /* ⚙️ 设置键右侧（左侧工具区） */
    if(mine && mine.parentElement===anchor.parentElement && anchor.nextElementSibling===mine) return;
    if(mine) mine.remove();
    if(!btns.length) return;
    var b=document.createElement('button');
    b.type='button'; b.id='lc-skillbtn'; b.innerHTML='🧩 技能';
    b.addEventListener('click',function(e){ e.stopPropagation(); toggle(ta); });
    anchor.parentElement.insertBefore(b, anchor.nextSibling);"""

assert old1 in html, 'ensureButton region not found'
html = html.replace(old1, new1, 1)

open('/tmp/lc_index_btn5.html', 'w', encoding='utf-8').write(html)
r2 = run('docker cp /tmp/lc_index_btn5.html librechat-api:' + INDEX)
if r2.returncode != 0:
    sys.exit('docker cp failed: ' + r2.stderr)
print('[v5: button anchor moved next to settings button]')
