#!/usr/bin/env python3
"""用量统计面板后端：读 LibreChat mongo，展示注册用户/消息数/token 消耗/趋势/最近提问。管理员专用。"""
import hashlib, hmac, json, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8766
BASE = Path('/opt/usagepanel')
PASS_FILE = BASE / 'pass.txt'
SECRET_FILE = BASE / 'secret.key'

_secret = SECRET_FILE.read_bytes().strip()

MONGO_JS = """
const d7 = new Date(Date.now() - 7*86400000);
const d14 = new Date(Date.now() - 14*86400000);
const users = db.users.find({}, {name:1,email:1,role:1,createdAt:1}).toArray();
const agg = db.messages.aggregate([
  {$group:{_id:"$user",
    msgs:{$sum:1}, tokens:{$sum:{$ifNull:["$tokenCount",0]}},
    q:{$sum:{$cond:["$isCreatedByUser",1,0]}},
    first:{$min:"$createdAt"}, last:{$max:"$createdAt"},
    convs:{$addToSet:"$conversationId"},
    msgs7:{$sum:{$cond:[{$gte:["$createdAt",d7]},1,0]}},
    tokens7:{$sum:{$cond:[{$gte:["$createdAt",d7]},{$ifNull:["$tokenCount",0]},0]}}}},
  {$project:{msgs:1,tokens:1,q:1,first:1,last:1,msgs7:1,tokens7:1,convs:{$size:"$convs"}}}
]).toArray();
const prev = db.messages.aggregate([
  {$match:{createdAt:{$gte:d14,$lt:d7}}},
  {$group:{_id:"$user", msgs:{$sum:1}, tokens:{$sum:{$ifNull:["$tokenCount",0]}}}}
]).toArray();
const daily = db.messages.aggregate([
  {$match:{createdAt:{$gte:d14}}},
  {$group:{_id:{$dateToString:{format:"%Y-%m-%d",date:"$createdAt",timezone:"+08:00"}},
    msgs:{$sum:1}, tokens:{$sum:{$ifNull:["$tokenCount",0]}}, us:{$addToSet:"$user"}}},
  {$project:{msgs:1,tokens:1,us:{$size:"$us"}}},
  {$sort:{_id:1}}
]).toArray();
const eps = db.messages.aggregate([{$group:{_id:{$ifNull:["$endpoint","未知"]},msgs:{$sum:1},tok:{$sum:{$ifNull:["$tokenCount",0]}}}}]).toArray();
const recent = db.messages.find({isCreatedByUser:true},
  {createdAt:1,user:1,text:1,attachments:1}).sort({createdAt:-1}).limit(10).toArray();
const tt = db.messages.aggregate([{$group:{_id:null,t:{$sum:{$ifNull:["$tokenCount",0]}}}}]).toArray();
JSON.stringify({users:users, agg:agg, prev:prev, daily:daily, eps:eps, recent:recent,
  totalMsgs: db.messages.countDocuments({}),
  msgs7: db.messages.countDocuments({createdAt:{$gte:d7}}),
  msgsPrev: db.messages.countDocuments({createdAt:{$gte:d14,$lt:d7}}),
  totalTok: (tt[0]||{t:0}).t,
  convs: db.conversations.countDocuments({})});
"""


def mongo_stats():
    out = subprocess.run(
        ['docker', 'exec', 'librechat-mongo', 'mongosh', '--quiet', 'LibreChat', '--eval', MONGO_JS],
        capture_output=True, text=True, timeout=20).stdout
    line = [l for l in out.splitlines() if l.strip().startswith('{')][-1]
    return json.loads(line)


def _token_ok(cookie_val):
    want = hmac.new(_secret, b'usage-admin', hashlib.sha256).hexdigest()
    return isinstance(cookie_val, str) and hmac.compare_digest(cookie_val, want)


PAGE = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Luma 用量统计</title><style>
*{box-sizing:border-box;margin:0}body{font-family:system-ui,'Microsoft YaHei';background:#f4f6f9;color:#1a2332}
.wrap{max-width:1150px;margin:28px auto;padding:0 16px}
h1{font-size:22px;margin-bottom:2px}h1 span{color:#6b7a90;font-size:13px;font-weight:400;margin-left:8px}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.upd{color:#8a97a8;font-size:12px}
button{padding:8px 20px;background:#0f6bff;color:#fff;border:0;border-radius:8px;font-size:13px;cursor:pointer}
button:hover{background:#0d5cd6}
.cards{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.card{background:#fff;border-radius:10px;padding:12px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08);min-width:140px;flex:1}
.card b{display:block;font-size:24px;color:#0f6bff}.card small{color:#6b7a90;font-size:12px}
.card .sub{font-size:11px;color:#8a97a8;margin-top:2px}
.up{color:#1a9e55}.down{color:#c0392b}
.panel{background:#fff;border-radius:10px;padding:14px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px}
.panel h3{font-size:14px;color:#3a4a5e;margin-bottom:12px}
.chart{display:flex;align-items:flex-end;gap:7px;height:110px}
.bw{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;height:100%;justify-content:flex-end}
.bar{width:70%;max-width:34px;background:linear-gradient(180deg,#4d94ff,#0f6bff);border-radius:3px 3px 0 0;min-height:2px}
.bar.today{background:linear-gradient(180deg,#ffc24d,#ff9800)}
.bl{font-size:10px;color:#8a97a8;white-space:nowrap}.bl b{color:#55657a;display:block;font-size:10px}
.cols{display:flex;gap:16px;flex-wrap:wrap}
.cols .panel{flex:1;min-width:320px;margin-bottom:0}
.chips span{display:inline-block;background:#eef4ff;color:#2a5db0;border-radius:14px;padding:4px 12px;font-size:12px;margin:0 8px 8px 0}
.qlist{list-style:none}.qlist li{padding:7px 0;border-bottom:1px solid #f0f3f7;font-size:12.5px}
.qlist li:last-child{border:0}.qt{color:#8a97a8;margin-right:6px;font-variant-numeric:tabular-nums}
.qn{color:#0f6bff;font-weight:600;margin-right:6px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px}
th,td{padding:9px 11px;text-align:left;font-size:12.5px;border-bottom:1px solid #eef1f5;white-space:nowrap}
th{background:#f8fafc;color:#55657a;font-weight:600}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:#f6faff}.role-ADMIN{color:#b45309;font-weight:600}
.note{color:#8a97a8;font-size:12px;margin-top:10px;line-height:1.7}
#login{max-width:320px;margin:120px auto;background:#fff;padding:28px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.1);text-align:center}
#login input{width:100%;padding:10px;margin:14px 0;border:1px solid #d7dee8;border-radius:8px;font-size:15px}
#err{color:#c0392b;font-size:13px;min-height:18px}
</style></head><body>
<div id="login" style="display:none"><h1>Luma 用量统计</h1>
<input id="pw" type="password" placeholder="管理密码" onkeydown="if(event.key=='Enter')doLogin()"><br>
<div id="err"></div><button onclick="doLogin()">进入</button></div>
<div class="wrap" id="app" style="display:none">
<div class="topbar"><h1>Luma 用量统计<span>团队 AI 管理面板 · 每 60 秒自动刷新</span></h1>
<div><span class="upd" id="upd"></span> <button onclick="load()">刷新</button></div></div>
<div class="cards" id="cards"></div>
<div class="panel"><h3>近 14 天每日消息</h3><div class="chart" id="chart"></div></div>
<table><thead><tr><th>用户</th><th>角色</th><th>注册</th><th class="num">会话</th><th class="num">提问</th>
<th class="num">消息总数</th><th class="num">Token 总数</th><th class="num">7天消息</th><th class="num">7天 Token</th>
<th>7天环比</th><th>最后活跃</th></tr></thead><tbody id="rows"></tbody></table>
<div class="cols">
<div class="panel"><h3>使用通道</h3><div class="chips" id="chips"></div></div>
<div class="panel"><h3>最近提问</h3><ul class="qlist" id="qlist"></ul></div>
</div>
<p class="note">Token 来自 LibreChat 记账（含上下文，仅网页端）；飞书/微信消息不计入。环比 = 近 7 天 vs 再前 7 天。仅管理员可见。</p>
</div>
<script>
const WD=['日','一','二','三','四','五','六'];
function fmt(n){return (n||0).toLocaleString()}
function fmtTok(n){if(!n)return '0';if(n>=10000)return (n/10000).toFixed(1)+' 万';return fmt(n)}
function fmtT(s){return s?String(s).replace('T',' ').slice(0,16):'—'}
function pct(a,b){if(!b)return '<span class="up">新增</span>';const p=Math.round((a-b)/b*100);
  if(p===0)return '<span style="color:#8a97a8">持平</span>';
  return p>0?`<span class="up">▲ ${p}%</span>`:`<span class="down">▼ ${-p}%</span>`}
async function load(){
try{
  const r = await fetch('api/stats');
  if(r.status===401){login();return}
  const d = await r.json();
  const agg={};d.agg.forEach(a=>agg[a._id]=a);
  const prev={};d.prev.forEach(a=>prev[a._id]=a);
  const name={};d.users.forEach(u=>name[u._id]=u.name||u.email);

  document.getElementById('cards').innerHTML =
    `<div class="card"><b>${d.users.length}</b><small>注册用户</small></div>`+
    `<div class="card"><b>${fmt(d.convs)}</b><small>会话数</small></div>`+
    `<div class="card"><b>${fmt(d.totalMsgs)}</b><small>累计消息</small></div>`+
    `<div class="card"><b>${fmtTok(d.totalTok)}</b><small>累计 Token</small></div>`+
    `<div class="card"><b>${fmt(d.msgs7)}</b><small>近 7 天消息</small><div class="sub">上周 ${fmt(d.msgsPrev)} ${pct(d.msgs7,d.msgsPrev)}</div></div>`+
    `<div class="card"><b>${fmtTok(d.agg.reduce((s,a)=>s+a.tokens7,0))}</b><small>近 7 天 Token</small></div>`+
    `<div class="card"><b>${d.agg.filter(a=>a.msgs7>0).length}</b><small>近 7 天活跃用户</small></div>`;

  // 14 天图(补零)
  const dm={};d.daily.forEach(x=>dm[x._id]=x);
  const days=[];let max=1;
  for(let i=13;i>=0;i--){const dt=new Date(Date.now()-i*86400000);
    const k=dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0')+'-'+String(dt.getDate()).padStart(2,'0');
    const v=dm[k]||{msgs:0,tokens:0,us:0};if(v.msgs>max)max=v.msgs;days.push({k,v,wd:WD[dt.getDay()],today:i===0});}
  document.getElementById('chart').innerHTML=days.map(x=>
    `<div class="bw" title="${x.k} 周${x.wd}：${x.v.msgs} 条消息 / ${fmtTok(x.v.tokens)} token / ${x.v.us} 人">
     <div class="bar${x.today?' today':''}" style="height:${Math.max(2,Math.round(x.v.msgs/max*96))}px"></div>
     <div class="bl"><b>${x.k.slice(5)}</b>${x.wd}</div></div>`).join('');

  const rows=d.users.slice().sort((a,b)=>String(agg[b._id]?.last||'').localeCompare(String(agg[a._id]?.last||''))).map(u=>{
    const a=agg[u._id]||{},p=prev[u._id]||{msgs:0};
    return `<tr><td><b>${u.name||'—'}</b><div style="color:#8a97a8;font-size:11px">${u.email}</div></td>`+
      `<td class="role-${u.role||'USER'}">${u.role||'USER'}</td>`+
      `<td>${fmtT(u.createdAt).slice(0,10)}</td>`+
      `<td class="num">${fmt(a.convs)}</td><td class="num">${fmt(a.q)}</td>`+
      `<td class="num">${fmt(a.msgs)}</td><td class="num">${fmtTok(a.tokens)}</td>`+
      `<td class="num">${fmt(a.msgs7)}</td><td class="num">${fmtTok(a.tokens7)}</td>`+
      `<td>${p.msgs? pct(a.msgs7,p.msgs)+' <span style="color:#8a97a8;font-size:11px">('+p.msgs+')</span>':'<span style="color:#8a97a8">—</span>'}</td>`+
      `<td>${fmtT(a.last)}</td></tr>`;
  }).join('');
  document.getElementById('rows').innerHTML=rows||'<tr><td colspan="11">还没有用户</td></tr>';

  const em={'Hermes':'网页端'};
  document.getElementById('chips').innerHTML=d.eps.map(e=>
    `<span>${em[e._id]||e._id} · ${fmt(e.msgs)} 条 / ${fmtTok(e.tok)} tk</span>`).join('')||'<span>暂无</span>';

  document.getElementById('qlist').innerHTML=d.recent.map(m=>{
    const t=(m.text||'').replace(/\\s+/g,' ').trim()||
      (m.attachments&&m.attachments.length?'[发送了附件/图片]':'[空]');
    return `<li><span class="qt">${fmtT(m.createdAt).slice(5,16)}</span>`+
      `<span class="qn">${name[m.user]||'?'}</span>${t.length>60?t.slice(0,60)+'…':t}</li>`;
  }).join('')||'<li>暂无提问</li>';

  document.getElementById('upd').textContent='更新于 '+new Date().toLocaleTimeString('zh-CN',{hour12:false});
  document.getElementById('app').style.display='block';
}catch(e){
  document.getElementById('app').style.display='block';
  document.getElementById('cards').innerHTML='<div class="card"><b>!</b><small>加载失败：'+e+'</small></div>';
}
}
async function doLogin(){
  const r = await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({password:document.getElementById('pw').value})});
  if(r.ok){load();setInterval(()=>{if(document.getElementById('app').style.display!=='none')load()},60000)}
  else{document.getElementById('err').textContent='密码不对'}
}
function login(){document.getElementById('login').style.display='block';document.getElementById('app').style.display='none';document.getElementById('pw').focus()}
load();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype='text/html; charset=utf-8', cookie=None):
        raw = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(raw)))
        if cookie:
            self.send_header('Set-Cookie', f'usage_auth={cookie}; Path=/; HttpOnly; SameSite=Lax')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/api/stats':
            cookie = (self.headers.get('Cookie') or '')
            val = dict(p.strip().split('=', 1) for p in cookie.split(';') if '=' in p).get('usage_auth')
            if not _token_ok(val):
                return self._send(401, '{"error":"unauthorized"}', 'application/json')
            try:
                return self._send(200, json.dumps(mongo_stats()), 'application/json')
            except Exception as e:
                return self._send(500, json.dumps({'error': str(e)}), 'application/json')
        return self._send(200, PAGE)

    def do_POST(self):
        if self.path != '/api/login':
            return self._send(404, 'not found')
        n = int(self.headers.get('Content-Length') or 0)
        try:
            data = json.loads(self.rfile.read(n))
        except Exception:
            return self._send(400, 'bad')
        real = PASS_FILE.read_text(encoding='utf-8').strip()
        if data.get('password') == real:
            tok = hmac.new(_secret, b'usage-admin', hashlib.sha256).hexdigest()
            return self._send(200, '{"ok":true}', 'application/json', cookie=tok)
        return self._send(403, '{"ok":false}', 'application/json')


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
