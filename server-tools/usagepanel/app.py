#!/usr/bin/env python3
"""用量统计面板后端：读 LibreChat mongo，展示注册用户/消息数/token 消耗。管理员专用。"""
import hashlib, hmac, json, subprocess, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8766
BASE = Path('/opt/usagepanel')
PASS_FILE = BASE / 'pass.txt'
SECRET_FILE = BASE / 'secret.key'

_secret = SECRET_FILE.read_bytes().strip()

MONGO_JS = """
const seven = new Date(Date.now() - 7*86400000);
const users = db.users.find({}, {name:1,email:1,role:1,createdAt:1}).toArray();
const agg = db.messages.aggregate([
  {$group:{_id:"$user", msgs:{$sum:1}, tokens:{$sum:{$ifNull:["$tokenCount",0]}},
    last:{$max:"$createdAt"},
    msgs7:{$sum:{$cond:[{$gte:["$createdAt",seven]},1,0]}},
    tokens7:{$sum:{$cond:[{$gte:["$createdAt",seven]},{$ifNull:["$tokenCount",0]},0]}}}}
]).toArray();
JSON.stringify({users:users, agg:agg,
  totalMsgs: db.messages.countDocuments({}),
  msgs7: db.messages.countDocuments({createdAt:{$gte:seven}}),
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


def _fmt_dt(iso):
    if not iso:
        return '—'
    return (iso[:10] + ' ' + iso[11:16]).replace('T', ' ')


PAGE = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Luma 用量统计</title><style>
*{box-sizing:border-box;margin:0}body{font-family:system-ui,'Microsoft YaHei';background:#f4f6f9;color:#1a2332}
.wrap{max-width:1080px;margin:32px auto;padding:0 16px}
h1{font-size:22px;margin-bottom:4px}h1 span{color:#6b7a90;font-size:13px;font-weight:400;margin-left:8px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}
.card{background:#fff;border-radius:10px;padding:14px 20px;box-shadow:0 1px 3px rgba(0,0,0,.08);min-width:150px}
.card b{display:block;font-size:26px;color:#0f6bff}.card small{color:#6b7a90}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}
th,td{padding:10px 12px;text-align:left;font-size:13px;border-bottom:1px solid #eef1f5;white-space:nowrap}
th{background:#f8fafc;color:#55657a;font-weight:600}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:#f6faff}.role-ADMIN{color:#b45309;font-weight:600}
.note{color:#8a97a8;font-size:12px;margin-top:12px}
#login{max-width:320px;margin:120px auto;background:#fff;padding:28px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.1);text-align:center}
#login input{width:100%;padding:10px;margin:14px 0;border:1px solid #d7dee8;border-radius:8px;font-size:15px}
button{padding:9px 22px;background:#0f6bff;color:#fff;border:0;border-radius:8px;font-size:14px;cursor:pointer}
#err{color:#c0392b;font-size:13px;min-height:18px}.refresh{float:right;padding:5px 14px;font-size:12px}
</style></head><body>
<div id="login" style="display:none"><h1>Luma 用量统计</h1>
<input id="pw" type="password" placeholder="管理密码" onkeydown="if(event.key=='Enter')doLogin()"><br>
<div id="err"></div><button onclick="doLogin()">进入</button></div>
<div class="wrap" id="app" style="display:none">
<h1>Luma 用量统计<span>团队 AI 管理面板</span><button class="refresh" onclick="load()">刷新</button></h1>
<div class="cards" id="cards"></div>
<table><thead><tr><th>用户</th><th>邮箱</th><th>角色</th><th>注册时间</th><th class="num">消息总数</th>
<th class="num">Token 总数</th><th class="num">7天消息</th><th class="num">7天 Token</th><th>最后活跃</th></tr></thead>
<tbody id="rows"></tbody></table>
<p class="note">Token 数据来自 LibreChat 记账（含上下文计入，仅网页端）；飞书/微信消息不计入。管理面板仅管理员可见。</p>
</div>
<script>
function fmt(n){return (n||0).toLocaleString()}
function fmtTok(n){if(!n)return '0';if(n>=10000)return (n/10000).toFixed(1)+' 万';return fmt(n)}
function fmtT(s){return s?String(s).replace('T',' ').slice(0,16):'—'}
async function load(){
  const r = await fetch('/api/stats');
  if(r.status===401){login();return}
  const d = (await r.json());
  const agg = {}; d.agg.forEach(a=>agg[a._id]=a);
  document.getElementById('cards').innerHTML =
    `<div class="card"><b>${d.users.length}</b><small>注册用户</small></div>`+
    `<div class="card"><b>${fmt(d.totalMsgs)}</b><small>累计消息</small></div>`+
    `<div class="card"><b>${fmt(d.msgs7)}</b><small>近 7 天消息</small></div>`+
    `<div class="card"><b>${d.agg.filter(a=>a.msgs7>0).length}</b><small>近 7 天活跃用户</small></div>`+
    `<div class="card"><b>${fmt(d.convs)}</b><small>会话数</small></div>`;
  const rows = d.users.map(u=>{
    const a = agg[u._id]||{};
    return `<tr><td>${u.name||'—'}</td><td>${u.email}</td>`+
      `<td class="role-${u.role||'USER'}">${u.role||'USER'}</td>`+
      `<td>${fmtT(u.createdAt)}</td>`+
      `<td class="num">${fmt(a.msgs)}</td><td class="num">${fmtTok(a.tokens)}</td>`+
      `<td class="num">${fmt(a.msgs7)}</td><td class="num">${fmtTok(a.tokens7)}</td>`+
      `<td>${fmtT(a.last)}</td></tr>`;
  }).join('');
  document.getElementById('rows').innerHTML = rows || '<tr><td colspan="9">还没有用户</td></tr>';
  document.getElementById('app').style.display='block';
}
async function doLogin(){
  const r = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({password:document.getElementById('pw').value})});
  if(r.ok){load()}else{document.getElementById('err').textContent='密码不对'}
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
