#!/usr/bin/env python3
"""Inject 用量統計 entry v3: 原生圖標——插入左欄工具欄圖標隊列尾部，與其他圖標同款式。"""
import re, subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'usage-link-2026c'

BLOCK = r"""<style>
/* PATCH-MARK: usage-link-2026c — 左欄工具欄原生用量圖標 */
#lc-usagebtn{border:none;background:transparent;cursor:pointer;color:inherit;display:flex;align-items:center;justify-content:center;padding:0;margin:0;}
#lc-usagebtn:hover{color:#E8590C !important;}
#lc-usagebtn svg{width:20px;height:20px;display:block;}
</style>
<button id="lc-usagebtn" title="用量統計（誰在用、用了多少）" aria-label="用量統計">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><line x1="18" y1="17" x2="18" y2="10"/><line x1="12" y1="17" x2="12" y2="5"/><line x1="6" y1="17" x2="6" y2="13"/></svg>
</button>
<script>
(function(){
  var b=document.getElementById('lc-usagebtn');
  if(!b) return;
  b.addEventListener('click',function(){ window.open('/usage/','_blank'); });
  function place(){
    var icons=document.querySelectorAll('nav a, nav button');
    var last=null, lastB=0;
    icons.forEach(function(el){
      var r=el.getBoundingClientRect();
      if(r.left<40 && r.width<70 && r.bottom>40 && r.bottom<window.innerHeight*0.72){
        if(r.bottom>lastB){ last=el; lastB=r.bottom; }
      }
    });
    if(last && last.parentElement){
      if(b.parentElement!==last.parentElement){ last.parentElement.appendChild(b); }
      var cs=getComputedStyle(last);
      b.style.position='static';
      b.style.width=cs.width; b.style.height=cs.height;
      b.style.margin=cs.margin; b.style.borderRadius=cs.borderRadius;
      b.style.color=cs.color; b.style.background='transparent';
      b.style.boxShadow='none'; b.style.left='auto'; b.style.top='auto';
    }else{
      /* 兜底：找不到圖標群時放左中側 */
      b.style.position='fixed'; b.style.left='0'; b.style.top='58%';
      b.style.width='34px'; b.style.height='52px'; b.style.color='#fff';
      b.style.background='linear-gradient(160deg,#ff7a29,#E8590C)';
      b.style.borderRadius='0 12px 12px 0';
      if(!b.parentElement || b.parentElement===document.body){ document.body.appendChild(b); }
    }
  }
  place();
  window.addEventListener('resize',place);
  setTimeout(place,800);
  setTimeout(place,2000);
  setInterval(function(){
    if(!document.body.contains(b)) { document.body.appendChild(b); }
    place();
  },3000);
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
s2 = re.sub(r'<style>\s*/\* PATCH-MARK: usage-link.*?</script>\s*', '', s, flags=re.S)
if MARK in s2:
    print('[usage link already present]')
    sys.exit(0)
if '</body>' not in s2:
    sys.exit('no </body> in index.html')
s2 = s2.replace('</body>', BLOCK + '\n</body>', 1)
write_index(s2)
print('[usage-link v3 injected (native toolbar icon)]')
