#!/usr/bin/env python3
"""Inject 用量統計 entry: 橙色標籤式按鈕貼在左欄圖標群尾部（自適應位置），點擊新標籤頁打開 /usage/。"""
import re, subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'usage-link-2026b'

BLOCK = r"""<style>
/* PATCH-MARK: usage-link-2026b — 左欄橙色用量統計入口（自適應位置） */
#lc-usagebtn{
  position:fixed;left:0;width:34px;height:52px;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;z-index:99990;color:#fff;
  background:linear-gradient(160deg,#ff7a29,#E8590C);
  border:none;border-radius:0 12px 12px 0;
  box-shadow:0 2px 10px rgba(232,89,12,.45);
  transition:width .15s;
}
#lc-usagebtn:hover{width:44px;}
#lc-usagebtn svg{width:19px;height:19px;}
</style>
<button id="lc-usagebtn" title="用量統計（誰在用、用了多少）" aria-label="用量統計">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><line x1="18" y1="17" x2="18" y2="10"/><line x1="12" y1="17" x2="12" y2="5"/><line x1="6" y1="17" x2="6" y2="13"/></svg>
</button>
<script>
(function(){
  var b=document.getElementById('lc-usagebtn');
  if(!b) return;
  b.addEventListener('click',function(){ window.open('/usage/','_blank'); });
  function place(){
    var best=0;
    document.querySelectorAll('nav a, nav button').forEach(function(el){
      var r=el.getBoundingClientRect();
      if(r.left<40 && r.width<70 && r.bottom<window.innerHeight*0.72){ best=Math.max(best,r.bottom); }
    });
    b.style.top=(best>0? best+14 : Math.round(window.innerHeight*0.56))+'px';
  }
  place();
  window.addEventListener('resize',place);
  setTimeout(place,1200);
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
    if 'lc-usagebtn' not in read_index():
        sys.exit('write verification failed (lc-usagebtn missing)')


s = read_index()
# 移除任何舊版 usage-link 注入塊（style→script 整段）
s2 = re.sub(r'<style>\s*/\* PATCH-MARK: usage-link.*?</script>\s*', '', s, flags=re.S)
if MARK in s2:
    print('[usage link already present]')
    sys.exit(0)
if '</body>' not in s2:
    sys.exit('no </body> in index.html')
s2 = s2.replace('</body>', BLOCK + '\n</body>', 1)
write_index(s2)
print('[usage-link v2 injected (orange, adaptive)]')
