#!/usr/bin/env python3
"""v2: robust time-based greeting — fuzzy match + interval retry."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'greet-welcome-2026b'

BLOCK = r"""<script>
/* PATCH-MARK: greet-welcome-2026b — 按时间问候 + 用户名（稳健版） */
(function(){
  var DONE=false;
  function hourGreet(){
    var h=new Date().getHours();
    if(h>=5 && h<12) return 'Good morning';
    if(h>=12 && h<18) return 'Good afternoon';
    return 'Good evening';
  }
  function findToken(){
    try{
      var ks=Object.keys(localStorage);
      for(var i=0;i<ks.length;i++){
        if(/token/i.test(ks[i])){
          var v=localStorage.getItem(ks[i]);
          if(v && v.indexOf('eyJ')===0) return v;
        }
      }
    }catch(e){}
    return null;
  }
  var NAME=null;
  function ensureName(cb){
    if(NAME!==null){cb(NAME);return;}
    var t=findToken();
    if(!t){cb('');return;}
    fetch('/api/user',{headers:{'Authorization':'Bearer '+t}})
      .then(function(r){return r.ok?r.json():null;})
      .then(function(d){ NAME=(d&&(d.name||d.username))||''; cb(NAME); })
      .catch(function(){cb('');});
  }
  function rewrite(){
    if(DONE) return;
    var hit=null;
    var walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null);
    while(walker.nextNode()){
      var t=(walker.currentNode.nodeValue||'').trim();
      if(t && t.length<40 && /^good day/i.test(t)){ hit=walker.currentNode; break; }
    }
    if(!hit) return;
    ensureName(function(name){
      hit.nodeValue=hourGreet()+(name?(', '+name):'');
      DONE=true;
    });
  }
  var mo=new MutationObserver(function(){ if(!DONE) setTimeout(rewrite,60); });
  function start(){
    if(document.body){
      mo.observe(document.body,{childList:true,subtree:true,characterData:true});
      var tries=0;
      var iv=setInterval(function(){ rewrite(); if(DONE || ++tries>60) clearInterval(iv); },1000);
    } else setTimeout(start,300);
  }
  start();
})();
</script>
"""

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read: ' + r.stderr)
html = r.stdout
if MARK in html:
    print('[greet v2 already present]')
    sys.exit(0)
assert '</head>' in html
html = html.replace('</head>', BLOCK + '\n</head>', 1)
open('/tmp/lc_index_greet2.html', 'w', encoding='utf-8').write(html)
r2 = run('docker cp /tmp/lc_index_greet2.html librechat-api:' + INDEX)
if r2.returncode != 0:
    sys.exit('docker cp failed: ' + r2.stderr)
print('[greeting v2 injected]')
