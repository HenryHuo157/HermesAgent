#!/usr/bin/env python3
"""Inject per-user scheduled-task panel (⏰ 定時) into LibreChat."""
import subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'tasks-panel-2026'

BLOCK = r"""<style>
/* PATCH-MARK: tasks-panel-2026 — 個人定時任務面板 */
#lc-taskbtn{
  display:inline-flex;align-items:center;gap:5px;
  border:1px solid rgba(16,185,129,.45);border-radius:999px;
  background:rgba(16,185,129,.08);color:#059669;
  font-size:12.5px;font-weight:600;
  padding:5px 12px;cursor:pointer;transition:all .15s;margin:0 4px;
}
#lc-taskbtn:hover{background:#059669;color:#fff;}
#lc-taskmask{position:fixed;inset:0;z-index:99998;background:rgba(10,14,22,.45);display:none;align-items:center;justify-content:center;}
#lc-taskpanel{
  width:min(560px,92vw);max-height:82vh;overflow-y:auto;
  background:#fff;border-radius:16px;box-shadow:0 24px 60px rgba(0,0,0,.25);
  padding:20px 22px;color:#1f2328;
}
@media (prefers-color-scheme: dark){ #lc-taskpanel{background:#161a22;color:#e6eaf2;} }
.tp-h{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
.tp-h b{font-size:16px;flex:1;}
.tp-x{border:none;background:none;font-size:20px;cursor:pointer;color:inherit;}
.tp-sub{font-size:12px;color:#8b93a5;margin-bottom:14px;}
.tp-row{border:1px solid rgba(130,140,160,.25);border-radius:12px;padding:10px 12px;margin-bottom:8px;}
.tp-name{font-weight:600;font-size:14px;}
.tp-meta{font-size:11.5px;color:#8b93a5;margin:3px 0 6px;}
.tp-acts{display:flex;gap:6px;flex-wrap:wrap;}
.tp-btn{border:1px solid rgba(130,140,160,.35);background:transparent;border-radius:8px;padding:3px 10px;font-size:12px;cursor:pointer;color:inherit;}
.tp-btn:hover{border-color:#10b981;color:#059669;}
.tp-btn.danger:hover{border-color:#ef4444;color:#dc2626;}
.tp-chip{font-size:10.5px;padding:1px 8px;border-radius:99px;margin-left:6px;}
.tp-chip.on{background:rgba(16,185,129,.12);color:#059669;}
.tp-chip.off{background:rgba(245,158,11,.15);color:#b45309;}
.tp-form{border-top:1px solid rgba(130,140,160,.25);margin-top:12px;padding-top:12px;}
.tp-form label{display:block;font-size:12px;font-weight:600;margin:8px 0 4px;color:inherit;}
.tp-form input,.tp-form select,.tp-form textarea{
  width:100%;box-sizing:border-box;border:1px solid rgba(130,140,160,.35);border-radius:9px;
  padding:8px 10px;font-size:13px;background:transparent;color:inherit;font-family:inherit;
}
.tp-form textarea{min-height:72px;resize:vertical;}
.tp-grid{display:flex;gap:8px;}
.tp-grid>div{flex:1;}
.tp-go{margin-top:12px;width:100%;padding:10px;border:none;border-radius:10px;background:#059669;color:#fff;font-size:14px;font-weight:600;cursor:pointer;}
.tp-msg{font-size:12.5px;margin-top:8px;color:#059669;min-height:16px;}
.tp-empty{text-align:center;color:#8b93a5;font-size:13px;padding:14px 0;}
#lc-taskresult{white-space:pre-wrap;font-size:12.5px;line-height:1.6;max-height:50vh;overflow-y:auto;background:rgba(130,140,160,.07);border-radius:10px;padding:12px;margin-top:10px;display:none;}
</style>
<script>
(function(){
  var MASK=null;
  function token(){
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
  function api(path, opts){
    var t=token(); if(!t) return Promise.reject('請先登入');
    opts=opts||{};
    opts.headers=Object.assign({'Authorization':'Bearer '+t}, opts.headers||{});
    return fetch('/tasksapi'+path, opts).then(function(r){ return r.json(); });
  }
  function cronDesc(c){
    var p=c.split(/\s+/);
    if(p.length<5) return c;
    var t=p[1]+':'+p[0], d=p[4];
    if(d==='*') return '每天 '+t;
    if(d==='1-5') return '工作日 '+t;
    var names=['日','一','二','三','四','五','六'];
    if(/^\d+$/.test(d)) return '每週'+names[+d%7]+' '+t;
    return c;
  }
  function ensureButton(){
    var ta=document.getElementById('prompt-textarea');
    if(!ta) return;
    var root=ta.closest('form')||(ta.parentElement&&ta.parentElement.parentElement)||ta.parentElement;
    var btns=root?root.querySelectorAll('button'):[];
    var mine=null, stale=document.querySelectorAll('#lc-taskbtn');
    for(var s=0;s<btns.length;s++){ if(btns[s].id==='lc-taskbtn') mine=btns[s]; }
    for(var d=0;d<stale.length;d++){ if(stale[d]!==mine) stale[d].remove(); }
    if(mine || !btns.length) return;
    var skill=document.getElementById('lc-skillbtn');
    var anchor=skill || btns[1] || btns[0];
    var b=document.createElement('button');
    b.type='button'; b.id='lc-taskbtn'; b.innerHTML='⏰ 定時';
    b.addEventListener('click',function(e){ e.stopPropagation(); openPanel(); });
    anchor.parentElement.insertBefore(b, anchor.nextSibling);
  }
  function openPanel(){
    if(!MASK){ buildMask(); }
    MASK.style.display='flex';
    refresh();
  }
  function closePanel(){ if(MASK) MASK.style.display='none'; }
  function buildMask(){
    MASK=document.createElement('div');
    MASK.id='lc-taskmask';
    MASK.innerHTML=
      '<div id="lc-taskpanel">'+
      '<div class="tp-h"><b>⏰ 我的定時任務</b><button class="tp-x" id="tp-close">×</button></div>'+
      '<div class="tp-sub">到點後 AI 自動執行，結果存到你的網盘，隨時回来看</div>'+
      '<div id="tp-list"><div class="tp-empty">載入中…</div></div>'+
      '<div id="lc-taskresult"></div>'+
      '<div class="tp-form">'+
      '<label>任務名稱</label><input id="tp-name" placeholder="例如：每早行業快訊" maxlength="40">'+
      '<label>要 AI 做什麼（到點自動執行）</label><textarea id="tp-prompt" placeholder="例如：搜尋 3 條家居行業新聞，每條一句話加來源連結"></textarea>'+
      '<label>頻率與時間</label>'+
      '<div class="tp-grid">'+
      '<div><select id="tp-freq"><option value="*">每天</option><option value="1-5">工作日（一至五）</option><option value="1">每週一</option><option value="2">每週二</option><option value="3">每週三</option><option value="4">每週四</option><option value="5">每週五</option><option value="6">每週六</option><option value="0">每週日</option></select></div>'+
      '<div><input id="tp-time" type="time" value="09:00"></div>'+
      '</div>'+
      '<button class="tp-go" id="tp-create">創建定時任務</button>'+
      '<div class="tp-msg" id="tp-msg"></div>'+
      '</div></div>';
    document.body.appendChild(MASK);
    MASK.addEventListener('click',function(e){ if(e.target===MASK) closePanel(); });
    MASK.querySelector('#tp-close').onclick=closePanel;
    MASK.querySelector('#tp-create').onclick=createTask;
  }
  function refresh(){
    api('/list').then(function(d){
      var el=MASK.querySelector('#tp-list');
      if(d.error){ el.innerHTML='<div class="tp-empty">'+d.error+'</div>'; return; }
      if(!d.tasks.length){ el.innerHTML='<div class="tp-empty">還沒有任務——在下面創建第一個 👇</div>'; return; }
      var h='';
      d.tasks.forEach(function(t){
        h+='<div class="tp-row">'+
           '<div class="tp-name">'+esc(t.name)+'<span class="tp-chip '+(t.status==='active'?'on':'off')+'">'+(t.status==='active'?'運行中':'已暫停')+'</span></div>'+
           '<div class="tp-meta">'+cronDesc(t.schedule)+' · 創建於 '+t.created+'</div>'+
           '<div class="tp-acts">'+
           '<button class="tp-btn" data-act="run" data-id="'+t.job_id+'" data-key="'+t.result_key+'">▶ 立即跑</button>'+
           '<button class="tp-btn" data-act="'+(t.status==='active'?'pause':'resume')+'" data-id="'+t.job_id+'">'+(t.status==='active'?'⏸ 暫停':'▶ 恢復')+'</button>'+
           '<button class="tp-btn" data-act="result" data-id="'+t.job_id+'" data-key="'+t.result_key+'">📄 看結果</button>'+
           '<button class="tp-btn danger" data-act="remove" data-id="'+t.job_id+'">🗑 刪除</button>'+
           '</div></div>';
      });
      el.innerHTML=h;
      el.querySelectorAll('.tp-btn').forEach(function(b){
        b.onclick=function(){
          var act=b.dataset.act;
          if(act==='result'){ showResult(b.dataset.key); return; }
          api('/action',{method:'POST',headers:{'Content-Type':'application/json'},
              body:JSON.stringify({job_id:b.dataset.id,action:act})}).then(function(r){
            if(act==='remove') b.closest('.tp-row').remove();
            else refresh();
          });
        };
      });
    }).catch(function(e){ MASK.querySelector('#tp-list').innerHTML='<div class="tp-empty">'+e+'</div>'; });
  }
  function showResult(key){
    api('/result/'+key).then(function(d){
      var el=MASK.querySelector('#lc-taskresult');
      el.style.display='block';
      el.textContent=d.result||'（空）';
    });
  }
  function createTask(){
    var name=MASK.querySelector('#tp-name').value.trim();
    var prompt=MASK.querySelector('#tp-prompt').value.trim();
    var freq=MASK.querySelector('#tp-freq').value;
    var time=MASK.querySelector('#tp-time').value||'09:00';
    var hm=time.split(':');
    var cron=parseInt(hm[1],10)+' '+parseInt(hm[0],10)+' * * '+freq;
    var msg=MASK.querySelector('#tp-msg');
    msg.textContent='創建中…';
    api('/create',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name:name,schedule:cron,prompt:prompt})}).then(function(r){
      if(r.ok){ msg.textContent='✅ 已創建！'; MASK.querySelector('#tp-name').value=''; MASK.querySelector('#tp-prompt').value=''; refresh(); }
      else msg.textContent='❌ '+(r.error||'失敗');
    }).catch(function(e){ msg.textContent='❌ '+e; });
  }
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  var mo=new MutationObserver(function(){ setTimeout(ensureButton,100); });
  function start(){ if(document.body){ mo.observe(document.body,{childList:true,subtree:true}); setTimeout(ensureButton,500); } else setTimeout(start,300); }
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
    print('[tasks panel already present]')
    sys.exit(0)
assert '</head>' in html
html = html.replace('</head>', BLOCK + '\n</head>', 1)
open('/tmp/lc_index_tasks.html', 'w', encoding='utf-8').write(html)
r2 = run('docker cp /tmp/lc_index_tasks.html librechat-api:' + INDEX)
if r2.returncode != 0:
    sys.exit('docker cp failed: ' + r2.stderr)
print('[tasks panel injected]')
