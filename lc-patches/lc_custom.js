#!/usr/bin/env node
/* ============================================================================
 * LibreChat 界面定制补丁 —— 唯一源文件 · 双模式（2026-10-07 零重启改造）
 * ============================================================================
 * 【浏览器模式】nginx 对页面注入 <script src="/lc_custom.js">（Cache-Control: no-cache），
 *   浏览器直接加载本文件、把 9 段补丁挂到页面上。
 *   改界面 = scp 本文件 + 写版本标记 —— 容器零重启、用户零打断。
 *
 * 【注入器模式（node，仅应急/迁移用）】默认 no-op（容器启动钩子保留但无操作）：
 *   node lc_custom.js --strip          剥离 index.html 内联注入块（迁移到浏览器模式时用一次）
 *   node lc_custom.js --inject-legacy  旧式内联注入（仅 nginx 分发不可用时的应急回退）
 *
 * 目录（9 段）：
 *   [head] hide-badges-2026     隐藏对 Hermes 无效的工具芯片行（纯 CSS）
 *   [head] tasks-panel-2026     ⏰ 定時任務面板 + 定時按钮
 *   [head] think-ui-2026b       思考块浅色小字、结束后自动收起（ZCode 风格，取代 thinking-style/working-verbs）
 *   [head] skills-picker-v7     🧩 技能选择器（按钮在定時鍵右侧）+ 白色 Artifact 卡片（取代 artifact-card/button-v5）
 *   [head] effort-selector-2026 🧠 思考程度选择器（点击循环 默认/关/低/中/高）
 *   [body] usage-link-2026c     用量统计悬浮贴签（可拖动，松手吸附左边；/usage/ 面板入口）
 *   [body] version-check-2026   📢 版本更新提示：每60秒查 /picasso-version.txt，有新版弹卡片，
 *                               用户点「立即更新」才刷新（deploy 脚本发布时写标记文件）；
 *                               右下角常驻版本徽章，点击随时手动检查/唤出更新卡片
 *   [body] dev-badge-2026       🚧 DEV 环境标识：仅 localhost:3082（SSH 隧道→nginx3082）显示，
 *                               右下角橙色胶囊（叠在版本徽章上方） + 顶部琥珀色细线；生产（443 端口）永不显示
 *   [body] desktop-pet-2026     🐾 桌面小宠物「小畢」：底部漫游、点击摸摸冒爱心、
 *                               双击睡觉、右键回家（刷新回来）；prefers-reduced-motion 不出场
 *
 * 版本约定：PATCH_VERSION 就是用户所见的版本号——每次改内容 +1；
 * deploy_lc_patches.py 发布时把它写进 /picasso-version.txt，
 * 所有打开着的旧页面会在 60 秒内弹「有新版本」，用户点「立即更新」/点徽章才刷新。
 * 段落用 String.raw 包裹——反斜杠原样保留；仍不要引入反引号 ` 和 ${ 字符，必要时转义。
 * ==========================================================================*/
'use strict';
var HEAD_SENTINEL = 'lc-custom:head:v1';
var BODY_SENTINEL = 'lc-custom:body:v1';
/* 内容版本号：改了任何段落内容就把这个数 +1。它同时是用户在版本徽章/弹窗里看到的版本号。 */
var PATCH_VERSION = 15;
var NODE_MODE = (typeof window === 'undefined' || typeof document === 'undefined');

/* 历史 PATCH-MARK —— 每次重打前剥掉，兼容老版本注入块（含本文件旧版） */
const LEGACY_MARKS = [
  'hide-badges-2026',
  'tasks-panel-2026',
  'think-ui-2026b',
  'usage-link-2026c',
  'skills-picker-v7',
  'effort-selector-2026',
  'skills-picker-v1',
  'skills-picker-v2',
  'skills-picker-v3',
  'skills-picker-v4',
  'skills-picker-v5',
  'skills-picker-v6',
  'thinking-thin-2026',
  'working-verbs-2026',
  'greet-welcome-2026b',
  'artifact-card-style-2026',
  'usage-link-2026d'
];

const SECTIONS = [
  { mark: 'hide-badges-2026', target: 'head', html: String.raw`
<style>
/* PATCH-MARK: hide-badges-2026 — 隐藏对 Hermes 无效的工具芯片行 */
.relative.flex.flex-wrap.items-center.gap-2:has(> .badge-icon){ display:none !important; }
</style>` },
  { mark: 'tasks-panel-2026', target: 'head', html: String.raw`
<style>
/* PATCH-MARK: tasks-panel-2026 — 個人定時任務面板 */
#lc-taskbtn{
  display:inline-flex;align-items:center;gap:5px;
  border:1px solid transparent;border-radius:999px;
  background:transparent;color:inherit;
  font-size:12.5px;font-weight:600;
  padding:5px 12px;cursor:pointer;transition:all .15s;margin:0 4px;
}
#lc-taskbtn:hover{background:rgba(128,128,128,.15);}
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
</script>` },
  { mark: 'think-ui-2026b', target: 'head', html: String.raw`
<style>
/* PATCH-MARK: think-ui-2026b — ZCode 风格思考块：浅色小字、紧凑 */
.group\/reasoning, .group\/reasoning-compact{
  font-size:12.5px !important;
  color:#9ca3af !important;
}
.group\/reasoning :is(p,span,div,li,ul,ol,blockquote,em,strong,b,i,h1,h2,h3,h4,h5,h6,td,th),
.group\/reasoning-compact :is(p,span,div,li,ul,ol,blockquote,em,strong,b,i){
  color:#9ca3af !important;
}
.group\/reasoning p, .group\/reasoning-compact p{
  margin:0 0 1px !important;
  line-height:1.6 !important;
}
.group\/reasoning a, .group\/reasoning-compact a{
  color:#8aa2c4 !important;
  text-decoration-color:rgba(138,162,196,.45) !important;
}
.group\/reasoning :is(code,pre), .group\/reasoning-compact :is(code,pre){
  font-size:11px !important;
  color:#9ca3af !important;
  background:rgba(130,140,160,.08) !important;
}
.group\/reasoning .rounded-lg, .group\/reasoning .rounded-2xl,
.group\/reasoning-compact .rounded-2xl{
  background:transparent !important;
  border-color:rgba(130,140,160,.16) !important;
}
.group\/reasoning blockquote, .group\/reasoning-compact blockquote{
  border-color:rgba(130,140,160,.25) !important;
}
.group\/reasoning button span{ color:#98a1b0 !important; }
.group\/reasoning-compact .tool-status-text{ color:#98a1b0 !important; font-weight:500 !important; }
</style>
<script>
/* PATCH-MARK: think-ui-2026b — 完成后收起 + 标题「思考 · 持續了 N 秒」 */
(function(){
  var MARK_RE = /思考了\s*(\d+)\s*秒/;
  function upgrade(block, anyStreaming){
    var leaves = block.querySelectorAll('p,div,span');
    var el = null, m = null;
    for (var j = 0; j < leaves.length; j++){
      if (leaves[j].querySelector('p,div,span')) continue;
      var mm = (leaves[j].textContent || '').match(MARK_RE);
      if (mm){ el = leaves[j]; m = mm; break; }
    }
    if (!el) return;
    if (el.style.display !== 'none') el.style.display = 'none';
    var label = block.querySelector('button[aria-expanded] span.truncate')
             || block.querySelector('.tool-status-text');
    if (label) label.textContent = '思考 · 持續了 ' + m[1] + ' 秒';
    // 已结束的消息才自动收起（生成中的保持展开，可实时看活动行）
    if (anyStreaming) return;
    if (!block.dataset.tuiCollapsed && !block.dataset.tuiUserToggled){
      var btn = block.querySelector('button[aria-expanded="true"]');
      if (btn){ block.dataset.tuiCollapsed = '1'; btn.click(); }
    }
  }
  function enhance(){
    var anyStreaming = !!document.querySelector('.submitting');
    var blocks = document.querySelectorAll('.group\\/reasoning, .group\\/reasoning-compact');
    for (var i = 0; i < blocks.length; i++) upgrade(blocks[i], anyStreaming);
  }
  document.addEventListener('click', function(e){
    var btn = e.target && e.target.closest && e.target.closest('.group\\/reasoning button, .group\\/reasoning-compact button');
    if (btn){
      var block = btn.closest('.group\\/reasoning, .group\\/reasoning-compact');
      if (block) block.dataset.tuiUserToggled = '1';
    }
  }, true);
  var t = null;
  var mo = new MutationObserver(function(){
    if (t) clearTimeout(t);
    t = setTimeout(enhance, 900);
  });
  function start(){
    if (document.body){ mo.observe(document.body, {childList:true, subtree:true}); enhance(); }
    else setTimeout(start, 300);
  }
  start();
})();
</script>` },
  { mark: 'skills-picker-v7', target: 'head', html: String.raw`
<style>
/* PATCH-MARK: skills-picker-v7 — 技能選擇器（與定時鍵並排）+ 白色卡片 */
#lc-skillbtn{
  display:inline-flex;align-items:center;gap:5px;
  border:1px solid transparent;border-radius:999px;
  background:transparent;color:inherit;
  font-size:12.5px;font-weight:600;
  padding:5px 12px;cursor:pointer;transition:all .15s;margin:0 4px;
}
#lc-skillbtn:hover{background:rgba(128,128,128,.15);}
#lc-skillbtn svg{width:15px;height:15px;display:block;}
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
/* #lc-skillbtn 样式统一在本段 <style> 顶部（与定時鍵同款透明胶囊） */
/* 白色 Artifact 卡片（覆蓋任何舊漸變版本） */
div:has(> button[data-artifact-trigger]){
  height:auto !important;
  margin:12px 0 !important;
  padding:14px 18px !important;
  border:1px solid rgba(120,120,140,.28);
  border-radius:14px;
  background:#ffffff !important;
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
  function ensureData(cb){
    /* 空结果不缓存——登录后立即打开可能撞上应用挂载期导致首拉失败，重试而不是永远空 */
    if(DATA && DATA.length){cb(DATA);return;}
    /* 双通道：Dev 走 /skills.json（容器 dist 靜態，picasso-dev-skills 注入）；
       生產 /skills.json 不存在 → 自動回退 /m/skills.json（nginx → /srv/hermes-share） */
    fetch('/skills.json').then(function(r){ if(!r.ok) throw 0; return r.json(); })
      .catch(function(){ return fetch('/m/skills.json').then(function(r){ return r.json(); }); })
      .then(function(d){
        DATA=d.skills||[];cb(DATA);
      })
      .catch(function(){cb([]);});
  }
  function composerRoot(ta){
    return ta.closest('form') || (ta.parentElement && ta.parentElement.parentElement) || ta.parentElement;
  }
  function ensureButton(){
    var ta=document.getElementById('prompt-textarea');
    if(!ta) return;
    /* v7: 錨點改為「⏰ 定時」按鈕——技能鍵固定在定時鍵右側；
       定時鍵還沒建立時先放左側設置鍵旁，任務面板建鍵後自動挪過去並排 */
    var scope=ta.closest('form')||composerRoot(ta)||document;
    var stale=document.querySelectorAll('#lc-skillbtn');
    var b=document.getElementById('lc-skillbtn');
    if(!b){
      b=document.createElement('button');
      b.type='button'; b.id='lc-skillbtn';
      b.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19.439 7.85c-.049.322.059.648.289.878l1.568 1.568c.47.47.706 1.087.706 1.704s-.235 1.233-.706 1.704l-1.611 1.611a.98.98 0 0 1-.837.276c-.47-.07-.802-.48-.968-.925a2.501 2.501 0 1 0-3.214 3.214c.446.166.855.497.925.968a.979.979 0 0 1-.276.837l-1.61 1.61a2.404 2.404 0 0 1-1.705.707 2.402 2.402 0 0 1-1.704-.706l-1.568-1.568a1.026 1.026 0 0 0-.877-.29c-.493.074-.84.504-1.02.968a2.5 2.5 0 1 1-3.237-3.237c.464-.18.894-.527.967-1.02a1.026 1.026 0 0 0-.289-.877l-1.568-1.568A2.402 2.402 0 0 1 1.998 12c0-.617.236-1.234.706-1.704L4.23 8.77c.24-.24.581-.353.917-.303.515.077.877.528 1.073 1.01a2.5 2.5 0 1 0 3.259-3.259c-.482-.196-.933-.558-1.012-1.073-.05-.336.062-.676.303-.917l1.525-1.525A2.402 2.402 0 0 1 12 1.998c.617 0 1.234.236 1.704.706l1.568 1.568c.23.23.556.338.877.29.493-.074.84-.504 1.02-.968a2.5 2.5 0 1 1 3.237 3.237c-.464.18-.894.527-.967 1.02Z"/></svg><span>skill</span>';
      b.addEventListener('click',function(e){ e.stopPropagation(); toggle(ta); });
    }
    var task=document.getElementById('lc-taskbtn');
    if(task && task.parentElement){
      for(var i=0;i<stale.length;i++){ if(stale[i]!==b) stale[i].remove(); }
      if(task.nextElementSibling!==b){ task.parentElement.insertBefore(b, task.nextSibling); }
      return;
    }
    /* 兜底：定時鍵不存在（任務面板未安裝/未就緒）時用左側錨點，
       但附件預覽展開時跳過——按鈕會被吸進預覽區變成幽靈芯片（v6b 踩過的坑） */
    var hasImg=scope.querySelector('img');
    if(hasImg){
      for(var j=0;j<stale.length;j++){ if(stale[j]!==b) stale[j].remove(); }
      return;
    }
    var btns=scope.querySelectorAll('button');
    if(!btns.length) return;
    var anchor=btns[1]||btns[0];   /* ⚙️ 设置键右侧 */
    if(b.parentElement===anchor.parentElement && anchor.nextElementSibling===b) return;
    anchor.parentElement.insertBefore(b, anchor.nextSibling);
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
        refresh();
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
    if(e.key==='ArrowDown'){ ACTIVE++; renderList(); e.preventDefault(); e.stopPropagation(); }
    else if(e.key==='ArrowUp'){ ACTIVE--; renderList(); e.preventDefault(); e.stopPropagation(); }
    else if(e.key==='Enter'){ if(ITEMS[ACTIVE]){ apply(ITEMS[ACTIVE]); } e.preventDefault(); e.stopPropagation(); }
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
</script>` },
  { mark: 'effort-selector-2026', target: 'head', html: String.raw`
<style>
/* PATCH-MARK: effort-selector-2026 — 思考程度選擇器（與定時/skill 並排） */
#lc-effortbtn{
  display:inline-flex;align-items:center;gap:5px;
  border:1px solid transparent;border-radius:999px;
  background:transparent;color:inherit;
  font-size:12.5px;font-weight:600;
  padding:5px 12px;cursor:pointer;
  transition:all .15s;margin:0 4px;
}
#lc-effortbtn:hover{background:rgba(128,128,128,.15);}
#lc-effortbtn.lc-on{border-color:rgba(232,89,12,.45);background:rgba(232,89,12,.08);}
#lc-effortbtn.lc-on:hover{background:rgba(232,89,12,.18);}
</style>
<script>
/* PATCH-MARK: effort-selector-2026 — 點擊循環 默認/關/低/中/高，攔截請求注入 reasoning_effort */
(function(){
  var LEVELS=['default','none','low','medium','high'];
  var LABELS={default:'默認',none:'關閉',low:'低',medium:'中',high:'高'};
  var KEY='lc-effort-level';
  function level(){ try{ var v=localStorage.getItem(KEY); return LEVELS.indexOf(v)>=0?v:'default'; }catch(e){ return 'default'; } }
  function render(b){
    var lv=level();
    b.innerHTML='🧠 思考·'+(LABELS[lv]||lv);
    if(lv==='default'){ b.classList.remove('lc-on'); } else { b.classList.add('lc-on'); }
  }
  function ensureButton(){
    var ta=document.getElementById('prompt-textarea');
    if(!ta) return;
    var skill=document.getElementById('lc-skillbtn');
    if(!skill || !skill.parentElement) return;
    var b=document.getElementById('lc-effortbtn');
    if(!b){
      b=document.createElement('button');
      b.type='button'; b.id='lc-effortbtn';
      b.title='思考程度：點擊切換（默認=跟隨系統設置 low）';
      b.addEventListener('click',function(e){
        e.stopPropagation();
        var next=LEVELS[(LEVELS.indexOf(level())+1)%LEVELS.length];
        try{ localStorage.setItem(KEY,next); }catch(err){}
        render(b);
      });
    }
    if(skill.nextElementSibling!==b){ skill.parentElement.insertBefore(b, skill.nextSibling); }
    render(b);
  }
  /* 攔截對話提交請求（v0.8.x：/api/agents/chat/<endpoint>），注入 reasoning_effort
     （default=不注入，跟隨系統配置） */
  if(!window.__lcEffortPatched){
    window.__lcEffortPatched=true;
    var _origFetch=window.fetch;
    window.fetch=function(input,init){
      try{
        var url=(typeof input==='string')?input:(input&&input.url)||'';
        var path=url.split('?')[0];
        var method=((init&&init.method)||(input&&input.method)||'GET').toUpperCase();
        if(init&&typeof init.body==='string'&&method==='POST'&&/\/api\/agents\/chat\/[a-z]+$/.test(path)){
          var lvl=level();
          if(lvl!=='default'){
            var parsed=JSON.parse(init.body);
            if(parsed&&typeof parsed==='object'&&!Array.isArray(parsed)){
              parsed.reasoning_effort=lvl;
              init=Object.assign({},init,{body:JSON.stringify(parsed)});
            }
          }
        }
      }catch(e){}
      return _origFetch.call(this,input,init);
    };
  }
  var mo=new MutationObserver(function(){ setTimeout(ensureButton,100); });
  function start(){
    if(document.body){ mo.observe(document.body,{childList:true,subtree:true}); setTimeout(ensureButton,500); }
    else setTimeout(start,300);
  }
  start();
})();
</script>` },
  { mark: 'usage-link-2026c', target: 'body', html: String.raw`
<style>
/* PATCH-MARK: usage-link-2026c — 用量統計懸浮貼籤（可拖動，鬆手吸附左邊） */
#lc-usagebtn{
  position:fixed;left:0;top:58%;z-index:9999;
  width:30px;height:52px;
  border:none;border-radius:0 12px 12px 0;
  background:linear-gradient(160deg,#ff7a29,#E8590C);
  color:#fff;cursor:grab;
  display:flex;align-items:center;justify-content:center;
  padding:0;margin:0;
  box-shadow:0 2px 8px rgba(232,89,12,.35);
  transition:left .25s ease, box-shadow .15s;
  touch-action:none;user-select:none;-webkit-user-select:none;
}
#lc-usagebtn:hover{box-shadow:0 3px 14px rgba(232,89,12,.5);}
#lc-usagebtn:active{cursor:grabbing;}
#lc-usagebtn svg{width:18px;height:18px;display:block;pointer-events:none;}
</style>
<button id="lc-usagebtn" title="用量統計（可拖動，鬆手吸附左邊）" aria-label="用量統計">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><line x1="18" y1="17" x2="18" y2="10"/><line x1="12" y1="17" x2="12" y2="5"/><line x1="6" y1="17" x2="6" y2="13"/></svg>
</button>
<script>
(function(){
  var b=document.getElementById('lc-usagebtn');
  if(!b) return;
  var KEY='lc-usage-tab-top';
  function clampTop(t){
    var h=b.offsetHeight||52, min=8, max=window.innerHeight-h-8;
    return Math.max(min, Math.min(t, max));
  }
  function currentTop(){
    return parseInt(getComputedStyle(b).top,10)||0;
  }
  function restore(){
    try{
      var v=parseInt(localStorage.getItem(KEY),10);
      if(!isNaN(v)) b.style.top=clampTop(v)+'px';
    }catch(e){}
  }
  var drag=null, moved=false;
  b.addEventListener('pointerdown',function(e){
    e.preventDefault();
    var r=b.getBoundingClientRect();
    drag={px:e.clientX, py:e.clientY, left:r.left, top:r.top, dx:e.clientX-r.left};
    moved=false;
    b.style.transition='none';
    try{ b.setPointerCapture(e.pointerId); }catch(err){}
  });
  b.addEventListener('pointermove',function(e){
    if(!drag) return;
    if(Math.abs(e.clientX-drag.px)>4 || Math.abs(e.clientY-drag.py)>4) moved=true;
    if(!moved) return;
    var maxX=window.innerWidth-b.offsetWidth;
    b.style.left=Math.max(0,Math.min(e.clientX-drag.dx,maxX))+'px';
    b.style.top=clampTop(drag.top+(e.clientY-drag.py))+'px';
  });
  function endDrag(){
    if(!drag) return;
    var wasMoved=moved;
    drag=null; moved=false;
    b.style.transition='';
    if(wasMoved){
      /* 鬆手吸附左邊，位置記住下次還在 */
      b.style.left='0px';
      try{ localStorage.setItem(KEY, String(clampTop(currentTop()))); }catch(err){}
    }else{
      /* 位移極小視為點擊。/usage/ 會被 Service Worker 劫持回 SPA 殼→404，
         /usage/index.html 是文件型請求，SW 放行，nginx 直接出面板 */
      var w=window.open('/usage/index.html','_blank');
      if(!w){ window.location.href='/usage/index.html'; }
    }
  }
  b.addEventListener('pointerup',endDrag);
  b.addEventListener('pointercancel',endDrag);
  window.addEventListener('resize',function(){
    if(!drag) b.style.top=clampTop(currentTop())+'px';
  });
  restore();
})();
</script>` },
  { mark: 'version-check-2026', target: 'body', html: String.raw`
<style>
/* PATCH-MARK: version-check-2026 — 版本更新提示卡片 + 常駐版本徽章（用戶點「立即更新」才刷新） */
#lc-verpill{
  position:fixed;right:12px;bottom:12px;z-index:99997;
  background:rgba(30,35,45,.78);color:#cbd5e1;
  font-size:11px;font-weight:600;letter-spacing:.3px;
  padding:3px 10px;border-radius:999px;cursor:pointer;
  user-select:none;-webkit-user-select:none;
  transition:background .2s,color .2s;
}
#lc-verpill:hover{background:rgba(30,35,45,.95);}
#lc-verpill.lc-ver-up{
  background:linear-gradient(160deg,#f59e0b,#d97706);
  color:#fff;box-shadow:0 2px 10px rgba(217,119,6,.4);
}
#lc-updatecard{
  position:fixed;right:20px;bottom:80px;z-index:99999;display:none;
  width:280px;background:#fff;border:1px solid #d5d9e0;border-radius:14px;
  box-shadow:0 12px 40px rgba(15,23,42,.22);
  padding:16px 18px;color:#1f2328;font-size:13px;line-height:1.5;
}
@media (prefers-color-scheme: dark){ #lc-updatecard{background:#161a22;color:#e6eaf2;border-color:#2a2f3a;} }
#lc-updatecard .uc-t{font-size:14.5px;font-weight:700;margin-bottom:4px;}
#lc-updatecard .uc-s{color:#8b93a5;font-size:12px;margin-bottom:12px;}
#lc-updatecard .uc-b{display:flex;gap:8px;}
#lc-updatecard button{flex:1;border-radius:9px;padding:8px 0;font-size:13px;font-weight:600;cursor:pointer;border:none;font-family:inherit;}
#lc-updatecard .uc-go{background:#059669;color:#fff;}
#lc-updatecard .uc-go:hover{background:#047857;}
#lc-updatecard .uc-later{background:transparent;color:inherit;border:1px solid rgba(130,140,160,.35);}
</style>
<script>
/* PATCH-MARK: version-check-2026 — 每60秒查 /picasso-version.txt（容器 dist 静态文件，
   deploy 脚本在重启就绪后才写入），发现比本页版本新就弹卡片；點「立即更新」才 reload，
   「稍後」靜默 1 小時。右下角常駐版本徽章：平時顯示當前版本號，有更新變橙色，
   點擊隨時手動檢查/喚出更新卡片（不受「稍後」靜默影響）。MINE 由注入器替换。 */
(function(){
  var MINE=__PATCH_VERSION__, KEY='lc-update-snooze';
  var card=null, pill=null, LATEST=MINE;
  function fmtPill(){
    if(LATEST>MINE){
      pill.textContent='v'+MINE+' ↑ v'+LATEST;
      pill.classList.add('lc-ver-up');
      pill.title='有新版本 v'+LATEST+'！點擊更新';
    }else{
      pill.textContent='v'+MINE;
      pill.title='當前版本 v'+MINE+'，點擊檢查更新';
    }
  }
  function show(){
    if(card){ card.style.display='block'; return; }
    card=document.createElement('div');
    card.id='lc-updatecard';
    card.innerHTML='<div class="uc-t">🎉 畢卡索有新版本</div>'+
      '<div class="uc-s">刷新後即可使用新版本，當前對話不受影響</div>'+
      '<div class="uc-b"><button class="uc-go">立即更新</button><button class="uc-later">稍後</button></div>';
    document.body.appendChild(card);
    card.querySelector('.uc-go').onclick=function(){
      try{ localStorage.removeItem(KEY); }catch(e){}
      location.reload();
    };
    card.querySelector('.uc-later').onclick=function(){
      try{ localStorage.setItem(KEY, String(Date.now()+60*60*1000)); }catch(e){}
      card.style.display='none';
    };
    card.style.display='block';
  }
  function check(fromUser){
    fetch('/picasso-version.txt?ts='+Date.now(), {cache:'no-store'})
      .then(function(r){ return r.ok ? r.text() : ''; })
      .then(function(t){
        var v=parseInt((t||'').trim(),10);
        if(!isNaN(v)) LATEST=v;
        fmtPill();
        if(isNaN(v) || v<=MINE){
          if(fromUser){
            pill.textContent='✓ 已是最新';
            setTimeout(fmtPill, 1500);
          }
          return;
        }
        if(fromUser){ show(); return; }   /* 手動點徽章：無視「稍後」靜默 */
        var snooze=0;
        try{ snooze=parseInt(localStorage.getItem(KEY),10)||0; }catch(e){}
        if(Date.now()<snooze) return;
        show();
      })
      .catch(function(){ if(fromUser){ pill.textContent='✓ 已是最新'; setTimeout(fmtPill, 1500); } });
  }
  function mount(){
    if(!document.body) return setTimeout(mount, 300);
    if(!pill){
      pill=document.createElement('div');
      pill.id='lc-verpill';
      pill.onclick=function(){ check(true); };
      document.body.appendChild(pill);
      fmtPill();
      check(false);
      setInterval(function(){ check(false); }, 60000);
    }
  }
  if(MINE>0){ mount(); }
})();
</script>` },
  { mark: 'dev-badge-2026', target: 'body', html: String.raw`
<style>
/* PATCH-MARK: dev-badge-2026 — DEV 環境標識（僅 localhost:3082 顯示，生產永不顯示） */
#lc-devbadge{
  position:fixed;right:12px;bottom:44px;z-index:99998;
  background:linear-gradient(160deg,#f59e0b,#d97706);
  color:#fff;font-size:12px;font-weight:700;letter-spacing:.5px;
  padding:5px 14px;border-radius:999px;
  box-shadow:0 2px 10px rgba(217,119,6,.4);
  cursor:help;user-select:none;-webkit-user-select:none;
}
#lc-devline{
  position:fixed;top:0;left:0;right:0;height:3px;z-index:99998;
  background:linear-gradient(90deg,#f59e0b,#d97706,#f59e0b);
  pointer-events:none;
}
</style>
<script>
/* PATCH-MARK: dev-badge-2026 — 埠號 3082（SSH 隧道→nginx3082→Dev容器，與生產同構）= Dev 環境才顯示；生產 443 端口不顯示 */
(function(){
  if(location.port !== '3082') return;
  function mount(){
    if(!document.body) return setTimeout(mount, 300);
    if(document.getElementById('lc-devbadge')) return;
    var line=document.createElement('div');
    line.id='lc-devline';
    document.body.appendChild(line);
    var b=document.createElement('div');
    b.id='lc-devbadge';
    b.textContent='🚧 DEV 環境';
    b.title='這是開發環境（localhost:3082），隨便折騰都不影響線上用戶';
    /* 版本徽章固定在右下 12px（version-check 段樣式），本徽章疊在其上方（樣式默認 bottom:44px） */
    document.body.appendChild(b);
  }
  mount();
})();
</script>` },
  { mark: 'desktop-pet-2026', target: 'body', html: String.raw`
<style>
/* PATCH-MARK: desktop-pet-2026 — 桌面小寵物「小畢」：底部漫遊、點擊摸摸、雙擊睡覺、右鍵回家 */
#lc-pet{position:fixed;bottom:8px;left:220px;z-index:99990;width:48px;height:42px;
  cursor:pointer;transition:left 1.1s cubic-bezier(.45,.05,.55,.95);
  user-select:none;-webkit-user-select:none;filter:drop-shadow(0 3px 4px rgba(30,27,75,.3));}
#lc-pet-body{position:absolute;left:2px;right:2px;bottom:2px;height:36px;
  background:linear-gradient(160deg,#818cf8,#4f46e5);
  border-radius:46% 46% 44% 44%/60% 60% 42% 42%;
  box-shadow:inset -4px -5px 0 rgba(30,27,75,.22);
  transform-origin:50% 100%;transition:transform .3s;}
#lc-pet.hopping #lc-pet-body{animation:pet-squash 1.15s ease;}
#lc-pet.love #lc-pet-body{animation:pet-jump .55s ease;}
@keyframes pet-squash{0%{transform:scaleY(.82) scaleX(1.12)}30%{transform:translateY(-10px) scaleY(1.06) scaleX(.96)}60%{transform:translateY(0) scaleY(.94) scaleX(1.04)}100%{transform:none}}
@keyframes pet-jump{0%{transform:none}35%{transform:translateY(-16px) rotate(-6deg)}70%{transform:translateY(0) scaleY(.85) scaleX(1.1)}100%{transform:none}}
.pet-eye{position:absolute;top:12px;width:9px;height:10px;background:#fff;border-radius:50%;}
.pet-eye.l{left:9px}.pet-eye.r{right:9px}
.pet-pupil{position:absolute;left:2.5px;top:3px;width:4.5px;height:4.5px;background:#1e1b4b;border-radius:50%;transition:transform .15s;}
#lc-pet.facing-r .pet-pupil{transform:translateX(1.5px)}
#lc-pet.facing-l .pet-pupil{transform:translateX(-1.5px)}
#lc-pet.sleeping .pet-eye{height:2.5px;top:16px;border-radius:2px;}
#lc-pet.sleeping .pet-pupil{opacity:0}
#lc-pet.sleeping #lc-pet-body{opacity:.85}
.pet-mouth{position:absolute;left:50%;top:24px;width:8px;height:4px;margin-left:-4px;
  border-bottom:2px solid #312e81;border-radius:0 0 8px 8px;}
.pet-cheek{position:absolute;top:19px;width:6px;height:3.5px;background:rgba(244,114,182,.75);border-radius:50%;}
.pet-cheek.l{left:5px}.pet-cheek.r{right:5px}
#lc-pet-bubble{position:absolute;left:50%;bottom:50px;transform:translateX(-50%);
  background:#fff;color:#1f2328;border:1px solid #d5d9e0;border-radius:10px;
  padding:5px 9px;font-size:11.5px;white-space:nowrap;display:none;
  box-shadow:0 4px 14px rgba(15,23,42,.15);}
#lc-pet-bubble:after{content:'';position:absolute;left:50%;bottom:-5px;margin-left:-5px;
  border:5px solid transparent;border-top-color:#fff;border-bottom:none;}
@media (prefers-color-scheme: dark){ #lc-pet-bubble{background:#161a22;color:#e6eaf2;border-color:#2a2f3a;} }
.pet-heart{position:fixed;z-index:99991;font-size:13px;pointer-events:none;animation:pet-float 1.2s ease forwards;}
@keyframes pet-float{0%{opacity:0;transform:translateY(0) scale(.6)}20%{opacity:1}100%{opacity:0;transform:translateY(-46px) scale(1.15)}}
#lc-pet-toast{position:fixed;left:50%;bottom:70px;transform:translateX(-50%);z-index:99999;
  background:rgba(30,35,45,.92);color:#fff;font-size:12.5px;padding:8px 16px;border-radius:10px;
  display:none;box-shadow:0 6px 20px rgba(0,0,0,.25);}
</style>
<div id="lc-pet" title="小畢 — 點我摸摸｜雙擊睡覺｜右鍵回家">
  <div id="lc-pet-body">
    <div class="pet-eye l"><div class="pet-pupil"></div></div>
    <div class="pet-eye r"><div class="pet-pupil"></div></div>
    <div class="pet-mouth"></div>
    <div class="pet-cheek l"></div><div class="pet-cheek r"></div>
  </div>
  <div id="lc-pet-bubble"></div>
</div>
<div id="lc-pet-toast"></div>
<script>
/* PATCH-MARK: desktop-pet-2026 — 漫遊循環：隨機跳/說話/打盹；互動見 title。減少動效用戶不出場 */
(function(){
  var pet=document.getElementById('lc-pet');
  if(!pet) return;
  if(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var bubble=document.getElementById('lc-pet-bubble');
  var WORDS=['在忙嗎？記得喝水 💧','摸魚一下也沒關係～','我今天很乖喔','點點我會開心 ✨','累了就休息一下','你好呀，我是小畢','升級不停機，就是這麼絲滑 ✨'];
  var sleeping=false, toastTimer=null;
  function clampX(x){ return Math.max(70, Math.min(x, window.innerWidth-70)); }
  function say(t){
    bubble.textContent=t; bubble.style.display='block';
    setTimeout(function(){ bubble.style.display='none'; }, 2600);
  }
  function hearts(n){
    var r=pet.getBoundingClientRect();
    for(var i=0;i<n;i++){
      var s=document.createElement('span');
      s.className='pet-heart';
      s.textContent=(i%2===0)?'❤️':'✨';
      s.style.left=(r.left+r.width/2+(Math.random()*30-15))+'px';
      s.style.top=(r.top-4)+'px';
      document.body.appendChild(s);
      (function(el){ setTimeout(function(){ el.remove(); }, 1250); })(s);
    }
  }
  function hop(){
    if(sleeping) return;
    var from=pet.getBoundingClientRect().left;
    var to=clampX(80+Math.random()*(window.innerWidth-160));
    pet.classList.add('hopping');
    pet.style.left=to+'px';
    pet.classList.toggle('facing-r', to>from);
    pet.classList.toggle('facing-l', to<from);
    setTimeout(function(){ pet.classList.remove('hopping'); }, 1200);
  }
  function nap(){
    sleeping=true; pet.classList.add('sleeping'); say('zZZ…');
    setTimeout(function(){ sleeping=false; pet.classList.remove('sleeping'); }, 5000+Math.random()*3000);
  }
  function loop(){
    var wait=1800+Math.random()*3200;
    setTimeout(function(){
      if(sleeping){ loop(); return; }
      var roll=Math.random();
      if(roll<0.62) hop();
      else if(roll<0.78) say(WORDS[Math.floor(Math.random()*WORDS.length)]);
      else nap();
      loop();
    }, wait);
  }
  pet.addEventListener('click', function(){
    if(sleeping){ sleeping=false; pet.classList.remove('sleeping'); say('嗯…我醒了'); return; }
    pet.classList.add('love');
    hearts(3);
    setTimeout(function(){ pet.classList.remove('love'); }, 560);
  });
  pet.addEventListener('dblclick', function(){
    sleeping=!sleeping;
    pet.classList.toggle('sleeping', sleeping);
    say(sleeping?'zZZ…':'精神滿滿！');
  });
  pet.addEventListener('contextmenu', function(e){
    e.preventDefault();
    pet.style.display='none';
    var t=document.getElementById('lc-pet-toast');
    t.textContent='小畢回家啦～重新整理頁面牠就回來';
    t.style.display='block';
    clearTimeout(toastTimer);
    toastTimer=setTimeout(function(){ t.style.display='none'; }, 2600);
  });
  window.addEventListener('resize', function(){
    var x=parseFloat(pet.style.left);
    if(!isNaN(x)) pet.style.left=clampX(x)+'px';
  });
  loop();
})();
</script>` }
];

/* ---- 通用清理：按 PATCH-MARK 剥掉历史注入块 ----
   锚定 <style> 内的 MARK 注释，一次性吞掉随后的 style(+)button(+)script 整块。
   块内不会出现 </style>，非贪婪匹配止于本块的第一个 </style>。 */
function stripMark(html, mark){
  const re = new RegExp(
    '<style>\\s*/\\* PATCH-MARK: ' + mark +
    '[\\s\\S]*?</style>' +                       /* CSS 段 */
    '(?:\\s*<button[\\s\\S]*?</button>)?' +       /* usage-link 的按钮 */
    '(?:\\s*<script>[\\s\\S]*?</script>)?\\n?',  /* 可选脚本段 */
    'g');
  return html.replace(re, '');
}

/* ============================================================
 * 浏览器模式：nginx sub_filter 注入的 <script src="/lc_custom.js"> 加载本文件，
 * 把全部段落的 HTML 挂到 body（style/元素走 innerHTML，script 重建后执行）。
 * ============================================================ */
if (!NODE_MODE) {
  function mountBrowser(){
    if (!document.body) return setTimeout(mountBrowser, 60);
    if (document.getElementById('lc-custom-mounted')) return;   /* 幂等 */
    var frag = SECTIONS.map(function(s){
      return s.html.replace(/__PATCH_VERSION__/g, String(PATCH_VERSION));
    }).join('\n');
    var host = document.createElement('div');
    host.id = 'lc-custom-mounted';
    host.style.display = 'none';
    host.innerHTML = frag;
    var scripts = [];
    Array.prototype.forEach.call(host.querySelectorAll('script'), function(s){
      scripts.push(s.textContent);
      s.parentNode.removeChild(s);
    });
    while (host.firstChild) document.body.appendChild(host.firstChild);
    scripts.forEach(function(code){
      var s = document.createElement('script');
      s.textContent = code;
      document.body.appendChild(s);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountBrowser);
  else mountBrowser();
}

/* ============================================================
 * Node 注入器模式（应急/迁移用，日常发布不走这里）
 * ============================================================ */
if (NODE_MODE) {
const fs = require('fs');
const INDEX = process.env.LC_INDEX_PATH || '/app/client/dist/index.html';

function stripAll(html){
  html = html.replace(new RegExp('<!-- ' + HEAD_SENTINEL + ' START -->[\\s\\S]*?<!-- ' + HEAD_SENTINEL + ' END -->\\n?', 'g'), '');
  html = html.replace(new RegExp('<!-- ' + BODY_SENTINEL + ' START -->[\\s\\S]*?<!-- ' + BODY_SENTINEL + ' END -->\\n?', 'g'), '');
  html = html.replace(new RegExp('<!-- lc-custom:patch-version:\\d+ -->\\n?', 'g'), '');
  for (const m of LEGACY_MARKS) html = stripMark(html, m);
  return html;
}

function writeIndex(html){
  const tmp = INDEX + '.lc-custom-tmp';
  fs.writeFileSync(tmp, html);
  fs.renameSync(tmp, INDEX);
}

function main(){
  let html;
  try {
    html = fs.readFileSync(INDEX, 'utf8');
  } catch (e) {
    console.error('[lc-custom] cannot read ' + INDEX + ': ' + e.message);
    process.exit(1);
  }

  /* --strip：只剥离内联注入块（迁移到浏览器模式时用一次），剥完即写回 */
  if (process.argv.indexOf('--strip') >= 0) {
    writeIndex(stripAll(html));
    console.log('[lc-custom] stripped inline blocks — browser mode (/lc_custom.js) takes over');
    return;
  }
  /* 日常默认 no-op（容器启动钩子安全空转）；应急回退需显式 --inject-legacy */
  if (process.argv.indexOf('--inject-legacy') < 0) {
    console.log('[lc-custom] injector retired (no-op). Use --strip or --inject-legacy.');
    return;
  }

  /* 0) 快速路径：全部标记齐全 + 哨兵在 + 版本号一致 = 已打过，什么都不做。
     改了任何段落内容后必须把 PATCH_VERSION +1，否则不会重新注入！ */
  const missing = SECTIONS.filter(s => html.indexOf('PATCH-MARK: ' + s.mark) < 0);
  const normalized = html.indexOf('<!-- ' + HEAD_SENTINEL) >= 0;
  const versioned = html.indexOf('lc-custom:patch-version:' + PATCH_VERSION) >= 0;
  if (missing.length === 0 && normalized && versioned) {
    console.log('[lc-custom] already applied (' + SECTIONS.length + '/' + SECTIONS.length + ' sections, v' + PATCH_VERSION + ')');
    return;
  }
  if (missing.length === 0) {
    console.log('[lc-custom] marks present but outdated (legacy format or older version) — re-injecting');
  }

  /* 1) 剥掉哨兵块（本脚本的旧注入）+ 版本戳 + 所有历史标记块 */
  html = stripAll(html);

  /* 2) 按 target 重新注入（__PATCH_VERSION__ 占位符替换为发布时版本号，
     version-check 段以此知道自己"是哪个版本"） */
  const ver = String(PATCH_VERSION);
  const headChunk = '<!-- lc-custom:patch-version:' + PATCH_VERSION + ' -->\n'
    + '<!-- ' + HEAD_SENTINEL + ' START -->\n'
    + SECTIONS.filter(s => s.target === 'head').map(s => s.html.replace(/__PATCH_VERSION__/g, ver)).join('\n')
    + '\n<!-- ' + HEAD_SENTINEL + ' END -->\n';
  const bodyChunk = '<!-- ' + BODY_SENTINEL + ' START -->\n'
    + SECTIONS.filter(s => s.target === 'body').map(s => s.html.replace(/__PATCH_VERSION__/g, ver)).join('\n')
    + '\n<!-- ' + BODY_SENTINEL + ' END -->\n';

  const hi = html.indexOf('</head>');
  if (hi < 0) throw new Error('</head> not found — LibreChat 结构变了？');
  html = html.slice(0, hi) + headChunk + html.slice(hi);

  const bi = html.indexOf('</body>');
  if (bi < 0) throw new Error('</body> not found');
  html = html.slice(0, bi) + bodyChunk + html.slice(bi);

  /* 3) 写回：index.html 可能是 root 属主，用临时文件 + rename（目录可写即可） */
  writeIndex(html);

  console.log('[lc-custom] injected ' + SECTIONS.length + ' sections (head '
    + SECTIONS.filter(s => s.target === 'head').length + ' + body '
    + SECTIONS.filter(s => s.target === 'body').length + ')');
}

try { main(); } catch (e) {
  console.error('[lc-custom] FAILED: ' + e.message);
  process.exit(1);
}
}
