#!/usr/bin/env python3
"""v4: fix filter wiring (search now actually filters) + move button to right side."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
OLD_MARK = 'skills-picker-v3'

BLOCK = r"""<style>
/* PATCH-MARK: skills-picker-v4 — 搜索过滤修复 + 按钮右置 */
#lc-skillpick{
  position:fixed;z-index:99999;display:none;
  background:#fff;border:1px solid #d5d9e0;border-radius:12px;
  box-shadow:0 10px 34px rgba(15,23,42,.18);
  max-height:380px;overflow:hidden;padding:0;
  display:flex;flex-direction:column;
}
@media (prefers-color-scheme: dark){
  #lc-skillpick{background:#161a22;border-color:#2a2f3a;}
  #lc-skillpick .sp-name{color:#e6eaf2;}
}
.sp-search{
  width:100%;box-sizing:border-box;
  border:none;border-bottom:1px solid #e5e7eb;
  padding:11px 14px;font-size:13.5px;outline:none;
  background:transparent;color:inherit;
}
.sp-search::placeholder{color:#a5abb8;}
.sp-list{overflow-y:auto;padding:6px;}
.sp-item{padding:8px 11px;border-radius:8px;cursor:pointer;}
.sp-item:hover,.sp-item.sp-on{background:rgba(99,102,241,.09);}
.sp-item.sp-on{outline:1px solid rgba(99,102,241,.35);}
.sp-name{font-size:13.5px;font-weight:600;color:#1f2328;}
.sp-desc{font-size:11.5px;color:#8b93a5;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.sp-none{color:#8b93a5;font-size:12.5px;cursor:default;padding:10px;}
#lc-skillbtn{
  display:inline-flex;align-items:center;gap:5px;
  border:1px solid rgba(99,102,241,.45);border-radius:999px;
  background:rgba(99,102,241,.08);color:#4f46e5;
  font-size:12.5px;font-weight:600;
  padding:5px 12px;cursor:pointer;
  transition:all .15s;margin:0 4px;
}
#lc-skillbtn:hover{background:#4f46e5;color:#fff;}
</style>
<script>
(function(){
  var DATA=null, DROP=null, ACTIVE=0, ITEMS=[], FILTER='', TA=null;
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function refresh(){
    ensureData(function(skills){
      var q=(FILTER||'').toLowerCase();
      ITEMS=skills.filter(function(s){
        return !q || s.name.toLowerCase().indexOf(q)>=0 || (s.desc||'').toLowerCase().indexOf(q)>=0;
      }).slice(0,80);
      ACTIVE=0;
      renderList();
    });
  }
  function composerRoot(ta){
    return ta.closest('form') || (ta.parentElement && ta.parentElement.parentElement) || ta.parentElement;
  }
  function ensureButton(){
    var ta=document.getElementById('prompt-textarea');
    if(!ta) return;
    var root=composerRoot(ta);
    var btns=root?root.querySelectorAll('button'):[];
    var stale=document.querySelectorAll('#lc-skillbtn');
    var mine=null;
    for(var s=0;s<btns.length;s++){ if(btns[s].id==='lc-skillbtn') mine=btns[s]; }
    for(var d=0;d<stale.length;d++){ if(stale[d]!==mine) stale[d].remove(); }
    if(mine || !btns.length) return;
    var send=btns[btns.length-1];           /* 发送键（最右） */
    var b=document.createElement('button');
    b.type='button'; b.id='lc-skillbtn'; b.innerHTML='🧩 技能';
    b.addEventListener('click',function(e){ e.stopPropagation(); toggle(ta); });
    send.parentElement.insertBefore(b, send);
  }
  function toggle(ta){
    if(DROP && DROP.style.display==='flex'){ hide(); } else { show(ta); }
  }
  function hide(){
    if(DROP) DROP.style.display='none';
    TA=null; ACTIVE=0; FILTER='';
    var si=DROP?DROP.querySelector('.sp-search'):null;
    if(si) si.value='';
  }
  function show(ta){
    TA=ta;
    buildDrop();
    var rect=ta.getBoundingClientRect();
    DROP.style.left=rect.left+'px';
    DROP.style.top=Math.max(8, rect.top-320)+'px';
    DROP.style.width=Math.max(380,rect.width)+'px';
    DROP.style.display='flex';
    var si=DROP.querySelector('.sp-search');
    if(si){ si.value=FILTER; si.focus(); }
    refresh();
  }
  function buildDrop(){
    if(DROP) return DROP;
    DROP=document.createElement('div');
    DROP.id='lc-skillpick';
    DROP.innerHTML='<input class="sp-search" placeholder="搜索技能…（支持中英文）"><div class="sp-list"></div>';
    DROP.addEventListener('input',function(e){
      if(e.target.classList.contains('sp-search')){
        FILTER=e.target.value.toLowerCase();
        ACTIVE=0; refresh();
      }
    });
    DROP.addEventListener('mousedown',function(e){
      var it=e.target.closest('.sp-item[data-i]');
      if(it){ e.preventDefault(); apply(ITEMS[parseInt(it.dataset.i,10)]); }
    });
    document.body.appendChild(DROP);
    return DROP;
  }
  function renderList(){
    var d=DROP; if(!d) return;
    var list=d.querySelector('.sp-list');
    if(ACTIVE>=ITEMS.length) ACTIVE=ITEMS.length-1;
    if(ACTIVE<0) ACTIVE=0;
    var h='';
    if(!ITEMS.length){ h+='<div class="sp-none">没有匹配的技能</div>'; }
    ITEMS.forEach(function(s,i){
      h+='<div class="sp-item'+(i===ACTIVE?' sp-on':'')+'" data-i="'+i+'">'+
         '<div class="sp-name">🧩 '+esc(s.name)+'</div>'+
         (s.desc?'<div class="sp-desc">'+esc(s.desc)+'</div>':'')+
         '</div>';
    });
    list.innerHTML=h;
    var on=list.querySelector('.sp-item.sp-on');
    if(on && on.scrollIntoView) on.scrollIntoView({block:'nearest'});
  }
  function setNativeValue(el, value){
    var proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(el, value);
    el.dispatchEvent(new Event('input', {bubbles:true}));
  }
  function apply(s){
    var el = document.getElementById('prompt-textarea') || TA;
    if(el && s){
      var v = '请使用「'+s.name+'」技能完成以下任务：\n';
      if('value' in el){ setNativeValue(el, v); } else { el.textContent = v; }
      el.focus();
    }
    hide();
  }
  document.addEventListener('input',function(e){
    var t=e.target;
    if(!t || !((t.tagName==='TEXTAREA') || t.id==='prompt-textarea')) return;
    var v=t.value||'';
    if(v==='/' || (v.charAt(0)==='/' && DROP && DROP.style.display==='flex')) show(t);
    else if(v.charAt(0)!=='/' && v.charAt(0)!=='…') hide();
  },true);
  document.addEventListener('keydown',function(e){
    if(!DROP || DROP.style.display!=='flex' || !TA) return;
    var inSearch = e.target.classList && e.target.classList.contains('sp-search');
    if(e.key==='ArrowDown'){ ACTIVE++; renderList(); e.preventDefault(); e.stopPropagation(); }
    else if(e.key==='ArrowUp'){ ACTIVE--; renderList(); e.preventDefault(); e.stopPropagation(); }
    else if(e.key==='Enter'){
      if(inSearch && ITEMS[ACTIVE]){ apply(ITEMS[ACTIVE]); }
      else if(!inSearch && ITEMS[ACTIVE]){ apply(ITEMS[ACTIVE]); }
      e.preventDefault(); e.stopPropagation();
    }
    else if(e.key==='Escape'){ hide(); e.stopPropagation(); }
  },true);
  document.addEventListener('click',function(e){
    if(DROP && DROP.style.display==='flex' && !DROP.contains(e.target) && e.target.id!=='lc-skillbtn') hide();
  });
  var mo=new MutationObserver(function(){ setTimeout(ensureButton,100); });
  function start(){
    if(document.body){
      mo.observe(document.body,{childList:true,subtree:true});
      setTimeout(ensureButton,500);
    } else { setTimeout(start,300); }
  }
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

start = html.find('<style>\n/* PATCH-MARK: ' + OLD_MARK)
if start < 0:
    sys.exit('old picker block not found')
end = html.find('</script>', start)
assert end > 0, 'old block end not found'
end += len('</script>')

html = html[:start] + BLOCK + html[end:]

open('/tmp/lc_index_picker_v4.html', 'w', encoding='utf-8').write(html)
r2 = run('docker cp /tmp/lc_index_picker_v4.html librechat-api:' + INDEX)
if r2.returncode != 0:
    sys.exit('docker cp failed: ' + r2.stderr)
print('[v4 picker installed]')
