#!/usr/bin/env python3
"""Inject 用量統計 entry (📊, left icon rail bottom) → opens /usage/ in a new tab."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'usage-link-2026'

BLOCK = r"""<style>
/* PATCH-MARK: usage-link-2026 — 左側圖標欄用量統計入口 */
#lc-usagebtn{
  position:fixed;left:0;bottom:18px;width:52px;height:44px;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;z-index:99990;color:#b8bcc4;background:transparent;border:none;
}
#lc-usagebtn:hover{color:#fff;background:rgba(255,255,255,.08);}
#lc-usagebtn svg{width:20px;height:20px;}
</style>
<button id="lc-usagebtn" title="用量統計（誰在用、用了多少）" aria-label="用量統計">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><line x1="18" y1="17" x2="18" y2="10"/><line x1="12" y1="17" x2="12" y2="5"/><line x1="6" y1="17" x2="6" y2="13"/></svg>
</button>
<script>
(function(){
  var b=document.getElementById('lc-usagebtn');
  if(!b) return;
  b.addEventListener('click',function(){ window.open('/usage/','_blank'); });
})();
</script>"""


def read_index():
    r = subprocess.run(['docker', 'exec', 'librechat-api', 'cat', INDEX],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('cannot read index.html: ' + r.stderr)
    return r.stdout


def write_index(s):
    r = subprocess.run(['docker', 'exec', '-i', '-u', 'root', 'librechat-api', 'sh', '-c', 'cat > ' + INDEX],
                       input=s, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('cannot write index.html: ' + r.stderr)
    # 校验写入后非空且标记存在——防静默截断
    chk = subprocess.run(['docker', 'exec', 'librechat-api', 'sh', '-c', 'wc -c ' + INDEX],
                         capture_output=True, text=True)
    if MARK not in read_index() or len(read_index()) < 5000:
        sys.exit('write verification failed: ' + chk.stdout)


s = read_index()
if MARK in s:
    print('[usage link already present]')
    sys.exit(0)
if '</body>' not in s:
    sys.exit('no </body> in index.html')
s = s.replace('</body>', BLOCK + '\n</body>', 1)
write_index(s)
print('[usage-link injected]')
