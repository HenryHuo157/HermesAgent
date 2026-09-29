#!/usr/bin/env python3
"""Inject Claude Code-style animated working verbs into LibreChat reasoning blocks."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'working-verbs-2026'

BLOCK = r"""<style>
/* PATCH-MARK: working-verbs-2026 — Claude Code style animated working verbs */
#lc-workword{
  display:flex;align-items:center;gap:7px;
  color:#8b93a5;font-size:12px;
  margin:6px 0 2px;
}
#lc-workword .ww-star{
  display:inline-block;animation:wstar 1.4s linear infinite;
  color:#8b93a5;font-size:13px;
}
@keyframes wstar{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}
#lc-workword .ww-word{animation:wwin .45s ease;}
@keyframes wwin{from{opacity:0;transform:translateY(2px)}to{opacity:1;transform:none}}
</style>
<script>
(function(){
  var WORDS=['Working…','Thinking…','Searching the web…','Reading files…','Writing code…','Running commands…','Analyzing results…','Polishing details…','Brewing something good…'];
  var i=0;
  function findTimer(root){
    var all=root.querySelectorAll('div,span');
    for(var j=0;j<all.length;j++){
      if(all[j].childElementCount!==0) continue;
      var t=(all[j].textContent||'').trim();
      if(/^\d{1,3}s$/.test(t)||/^\d+m\s+\d{1,3}s$/.test(t)) return all[j];
    }
    return null;
  }
  function ensureHost(timer){
    var host=timer.parentElement;
    if(!host) return null;
    var ex=host.querySelector(':scope > #lc-workword');
    if(ex) return ex;
    var d=document.createElement('div');
    d.id='lc-workword';
    d.innerHTML='<span class="ww-star">✳</span><span class="ww-word"></span>';
    host.insertBefore(d, timer);
    return d;
  }
  function tick(){
    try{
      var containers=document.querySelectorAll('.group\\/reasoning, .group\\/reasoning-compact');
      for(var k=0;k<containers.length;k++){
        var c=containers[k];
        var timer=findTimer(c);
        if(!timer) continue;
        var w=ensureHost(timer);
        if(w){
          i=(i+1)%WORDS.length;
          var wordEl=w.querySelector('.ww-word');
          if(wordEl) wordEl.textContent=WORDS[i];
        }
      }
    }catch(e){}
  }
  setInterval(tick,1200);
  var mo=new MutationObserver(function(){ setTimeout(tick,150); });
  function start(){ if(document.body){ mo.observe(document.body,{childList:true,subtree:true}); tick(); } else { setTimeout(start,300); } }
  start();
})();
</script>
"""

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read index.html: ' + r.stderr)
html = r.stdout

if MARK in html:
    print('[working-verbs already present]')
else:
    assert '</head>' in html, 'no </head>'
    html = html.replace('</head>', BLOCK + '\n</head>', 1)
    open('/tmp/lc_index_v3.html', 'w', encoding='utf-8').write(html)
    r2 = run('docker cp /tmp/lc_index_v3.html librechat-api:' + INDEX)
    if r2.returncode != 0:
        sys.exit('docker cp failed: ' + r2.stderr)
    print('[working-verbs injected]')
