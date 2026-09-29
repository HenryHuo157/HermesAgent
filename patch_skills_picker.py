#!/usr/bin/env python3
"""Inject a '/' skill-picker dropdown into LibreChat's composer."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'skills-picker-2026'

BLOCK = r"""<style>
/* PATCH-MARK: skills-picker-2026 — / 技能选择器 */
#lc-skillpick{
  position:fixed;z-index:99999;display:none;
  background:#fff;border:1px solid #d5d9e0;border-radius:12px;
  box-shadow:0 10px 34px rgba(15,23,42,.18);
  max-height:340px;overflow-y:auto;padding:6px;
}
@media (prefers-color-scheme: dark){
  #lc-skillpick{background:#161a22;border-color:#2a2f3a;}
  #lc-skillpick .sp-name{color:#e6eaf2;}
}
.sp-head{font-size:11px;color:#8b93a5;padding:6px 10px 4px;}
.sp-item{padding:7px 10px;border-radius:8px;cursor:pointer;}
.sp-item:hover,.sp-item.sp-on{background:rgba(99,102,241,.09);}
.sp-item.sp-on{outline:1px solid rgba(99,102,241,.35);}
.sp-name{font-size:13.5px;font-weight:600;color:#1f2328;}
.sp-desc{font-size:11.5px;color:#8b93a5;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.sp-none{color:#8b93a5;font-size:12.5px;cursor:default;padding:8px 10px;}
</style>
<script>
(function(){
  var DATA=null, DROP=null, ACTIVE=0, ITEMS=[], TA=null;
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function ensureData(cb){
    if(DATA){cb(DATA);return;}
    fetch('/m/skills.json').then(function(r){return r.json();}).then(function(d){
      DATA=d.skills||[];cb(DATA);
    }).catch(function(){cb([]);});
  }
  function buildDrop(){
    if(DROP) return DROP;
    DROP=document.createElement('div');
    DROP.id='lc-skillpick';
    document.body.appendChild(DROP);
    return DROP;
  }
  function hide(){ if(DROP) DROP.style.display='none'; TA=null; ACTIVE=0; }
  function show(ta){
    TA=ta;
    ensureData(function(skills){
      var q=ta.value.slice(1).toLowerCase();
      ITEMS=skills.filter(function(s){
        return !q || s.name.toLowerCase().indexOf(q)>=0 || (s.desc||'').toLowerCase().indexOf(q)>=0;
      }).slice(0,80);
      ACTIVE=0;
      var d=buildDrop();
      var rect=ta.getBoundingClientRect();
      d.style.left=rect.left+'px';
      d.style.top=Math.max(8, rect.top-300)+'px';
      d.style.width=Math.max(360,rect.width)+'px';
      render();
      d.style.display='block';
    });
  }
  function render(){
    var d=DROP; if(!d) return;
    if(ACTIVE>=ITEMS.length) ACTIVE=ITEMS.length-1;
    if(ACTIVE<0) ACTIVE=0;
    var h='<div class="sp-head">技能列表 · ↑↓ 选择 · Enter 确认 · Esc 关闭</div>';
    if(!ITEMS.length){ h+='<div class="sp-item sp-none">没有匹配的技能</div>'; }
    ITEMS.forEach(function(s,i){
      h+='<div class="sp-item'+(i===ACTIVE?' sp-on':'')+'" data-i="'+i+'">'+
         '<div class="sp-name">🧩 '+esc(s.name)+'</div>'+
         (s.desc?'<div class="sp-desc">'+esc(s.desc)+'</div>':'')+
         '</div>';
    });
    d.innerHTML=h;
    var on=d.querySelector('.sp-item.sp-on');
    if(on && on.scrollIntoView) on.scrollIntoView({block:'nearest'});
  }
  function apply(s){
    if(TA && s){
      TA.value='请使用「'+s.name+'」技能完成以下任务：\n';
      TA.focus();
      try{ TA.dispatchEvent(new Event('input',{bubbles:true})); }catch(e){}
    }
    hide();
  }
  document.addEventListener('input',function(e){
    var t=e.target;
    if(!t || t.tagName!=='TEXTAREA') return;
    var v=t.value||'';
    if(v==='/' || (v.charAt(0)==='/' && DROP && DROP.style.display==='block')) show(t);
    else hide();
  },true);
  document.addEventListener('keydown',function(e){
    if(!DROP || DROP.style.display!=='block' || !TA) return;
    if(e.key==='ArrowDown'){ ACTIVE++; render(); e.preventDefault(); e.stopPropagation(); }
    else if(e.key==='ArrowUp'){ ACTIVE--; render(); e.preventDefault(); e.stopPropagation(); }
    else if(e.key==='Enter'){ if(ITEMS[ACTIVE]){ apply(ITEMS[ACTIVE]); e.preventDefault(); e.stopPropagation(); } }
    else if(e.key==='Escape'){ hide(); e.stopPropagation(); }
  },true);
  document.addEventListener('click',function(e){
    if(DROP && DROP.style.display==='block' && !DROP.contains(e.target) && e.target!==TA) hide();
  });
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
    print('[skills picker already present]')
else:
    assert '</head>' in html, 'no </head>'
    html = html.replace('</head>', BLOCK + '\n</head>', 1)
    open('/tmp/lc_index_picker.html', 'w', encoding='utf-8').write(html)
    r2 = run('docker cp /tmp/lc_index_picker.html librechat-api:' + INDEX)
    if r2.returncode != 0:
        sys.exit('docker cp failed: ' + r2.stderr)
    print('[skills picker injected]')
