#!/usr/bin/env python3
"""Picasso 改密码服务：用户凭「当前密码 + 新密码」自助修改 LibreChat 登录密码，改完立即生效。

架构（与 usagepanel 同款零依赖模式）：
  浏览器 → nginx（/pw/）→ 本服务（127.0.0.1，Python stdlib http.server）
        → docker exec librechat-api node（bcryptjs 校验当前密码 + 写新 hash 到 users 表）

为什么这样做：LibreChat v0.8.8-rc4 没有内置"登录后改密码"功能，只有邮件重置
（且本服务器未配 SMTP）；服务器密码是 bcrypt，mongosh 无法校验，必须借
LibreChat 容器内的 bcryptjs。同一份代码 --dev/--prod 自动连接各自库。

安全：
  - 只绑 127.0.0.1，仅经 nginx 暴露（Dev 经隧道 3082，生产经 443 https）
  - 同一邮箱连续失败 5 次锁定 15 分钟（防在线爆破）
  - 用户不存在与密码错误返回同一提示（不泄露账号是否存在）
  - 日志只记邮箱与结果，绝不记密码

用法：
    python3 app.py --dev     # 端口 8768，容器 librechat-dev-api
    python3 app.py --prod    # 端口 8767，容器 librechat-api
"""
import argparse, json, re, subprocess, sys, threading, time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTAINERS = {
    'dev': {'api': 'librechat-dev-api', 'mongo': 'librechat-dev-mongo', 'db': 'LibreChatDev', 'port': 8768},
    'prod': {'api': 'librechat-api', 'mongo': 'librechat-mongo', 'db': 'LibreChat', 'port': 8767},
}
MAX_FAILS, LOCK_SECONDS = 5, 15 * 60
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# 在 LibreChat 容器内执行：stdin 收 {email,currentPassword,newPassword}
NODE_JS = r"""
const mongodb = require('/app/node_modules/mongodb');
const bcrypt = require('/app/node_modules/bcryptjs');
(async () => {
  const { email, currentPassword, newPassword } = JSON.parse(require('fs').readFileSync(0, 'utf8'));
  const client = new mongodb.MongoClient(process.env.MONGO_URI, { serverSelectionTimeoutMS: 5000 });
  await client.connect();
  const col = client.db().collection('users');
  const user = await col.findOne({ email: String(email).toLowerCase() });
  let ok = false;
  if (user && typeof user.password === 'string' && user.password.startsWith('$2')) {
    ok = await bcrypt.compare(String(currentPassword), user.password);
  }
  if (!ok) {
    console.log('RESULT:' + JSON.stringify({ ok: false, error: 'current' }));
  } else {
    await col.updateOne({ _id: user._id },
      { $set: { password: bcrypt.hashSync(String(newPassword), 10), updatedAt: new Date() },
        $unset: { mustChangePassword: '' } });
    console.log('RESULT:' + JSON.stringify({ ok: true }));
  }
  await client.close();
})().catch(() => console.log('RESULT:' + JSON.stringify({ ok: false, error: 'server' })));
"""

_fail = {}          # email_lower -> [fail_count, lock_until_ts]
_fail_lock = threading.Lock()
_exec_lock = threading.Lock()   # docker exec 全局串行，避免并发堆积
_container = None
_mongo = None
_db = None

PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>畢卡索 AI · 修改密码</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
       font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#ffffff;color:#1f2937}
  .card{background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;padding:32px;
        width:min(420px,92vw);box-shadow:0 10px 30px rgba(0,0,0,.08)}
  h1{font-size:20px;margin:0 0 4px;color:#111827}
  .sub{font-size:13px;color:#6b7280;margin:0 0 22px;line-height:1.6}
  label{display:block;font-size:13px;color:#374151;margin:14px 0 6px}
  input{width:100%;padding:11px 12px;border-radius:8px;border:1px solid #d1d5db;
        background:#ffffff;color:#111827;font-size:14px;outline:none}
  input:focus{border-color:#3b82f6}
  button{margin-top:22px;width:100%;padding:12px;border:0;border-radius:8px;
         background:#3b82f6;color:#fff;font-size:15px;font-weight:600;cursor:pointer}
  button:hover{background:#2f6fe0}
  button:disabled{background:#93c5fd;cursor:not-allowed}
  .msg{margin-top:16px;padding:11px 13px;border-radius:8px;font-size:13.5px;display:none;line-height:1.6}
  .ok{background:#ecfdf5;border:1px solid #a7f3d0;color:#047857;display:block}
  .err{background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;display:block}
  .tip{font-size:12px;color:#9ca3af;margin-top:18px;line-height:1.7}
</style></head><body>
<div class="card">
  <h1>畢卡索 AI · 修改密码</h1>
  <p class="sub">凭当前密码即可自助修改登录密码，<b>修改后立即生效</b>，请用新密码重新登录。</p>
  <form id="f" autocomplete="off">
    <label>邮箱（登录账号）</label>
    <input id="email" type="email" required placeholder="name@mainplan.com.hk">
    <label>当前密码</label>
    <input id="cur" type="password" required placeholder="管理员发给你的初始密码">
    <label>新密码（至少 8 位）</label>
    <input id="new" type="password" required minlength="8" placeholder="8 位以上，建议字母+数字混合">
    <label>确认新密码</label>
    <input id="new2" type="password" required minlength="8" placeholder="再输入一次新密码">
    <button id="btn" type="submit">确认修改</button>
  </form>
  <div id="msg" class="msg"></div>
  <p class="tip">· 新旧密码不能相同；连续输错 5 次当前密码会锁定 15 分钟。<br>
     · 主界面：<span style="color:#6b7280">https://47.243.79.144</span>（用邮箱 + 密码登录）</p>
</div>
<script>
const $=id=>document.getElementById(id);
$('f').addEventListener('submit', async e=>{
  e.preventDefault();
  const msg=$('msg'), btn=$('btn');
  const np=$('new').value;
  if(np!==$('new2').value){ msg.className='msg err'; msg.textContent='两次输入的新密码不一致。'; return; }
  if(np===$('cur').value){ msg.className='msg err'; msg.textContent='新密码不能与当前密码相同。'; return; }
  btn.disabled=true; btn.textContent='提交中…'; msg.className='msg';
  try{
    const r=await fetch('/pw/api/change',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:$('email').value.trim(),currentPassword:$('cur').value,newPassword:np})});
    const d=await r.json();
    if(d.ok){
      msg.className='msg ok';
      msg.textContent='✅ 密码已修改并立即生效！正在跳转到登录页…';
      $('f').reset();
      btn.disabled=true;
      setTimeout(function(){ location.href=location.origin+'/login'; }, 1500);
    }else{
      msg.className='msg err';
      msg.textContent={current:'当前密码不正确（或该邮箱没有设置密码登录）。注意：连续错 5 次将锁定 15 分钟。',
                       invalid:'新密码太短：请至少 8 位。',
                       locked:'失败次数过多，已临时锁定，请 15 分钟后再试。',
                       server:'服务器开小差了，请稍后重试；若持续失败请联系管理员。'}[d.error]||'修改失败，请重试。';
    }
  }catch(_){
    msg.className='msg err'; msg.textContent='网络异常，请检查连接后重试。';
  }
  btn.disabled=false; btn.textContent='确认修改';
});
</script></body></html>"""


def call_librechat(email, current, new):
    payload = json.dumps({'email': email, 'currentPassword': current, 'newPassword': new})
    with _exec_lock:
        proc = subprocess.run(
            ['docker', 'exec', '-i', _container, 'node', '/tmp/pw_change.node.js'],
            input=payload, capture_output=True, text=True, timeout=30)
    for line in proc.stdout.splitlines():
        if line.startswith('RESULT:'):
            return json.loads(line[len('RESULT:'):])
    return {'ok': False, 'error': 'server'}


def must_change(email):
    """查该邮箱是否仍带 mustChangePassword 标记（供界面横幅轮询）。"""
    safe = re.sub(r'[^a-zA-Z0-9@._+-]', '', email)  # 拼 mongosh --eval 前清洗
    js = 'JSON.stringify(db.users.find({email:"%s"},{mustChangePassword:1,_id:0}).toArray())' % safe
    with _exec_lock:
        proc = subprocess.run(
            ['docker', 'exec', _mongo, 'mongosh', '--quiet', _db, '--eval', js],
            capture_output=True, text=True, timeout=15)
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith('['):
            try:
                arr = json.loads(line)
                return bool(arr) and arr[0].get('mustChangePassword') is True
            except Exception:
                return False
    return False


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype='text/html; charset=utf-8'):
        data = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip('/') == '/pw':
            self._send(200, PAGE)
        elif self.path.startswith('/pw/api/must-change?'):
            try:
                qs = dict(p.split('=', 1) for p in self.path.split('?', 1)[1].split('&') if '=' in p)
                email = urllib.parse.unquote(qs.get('email', '')).strip().lower()
            except Exception:
                email = ''
            if not EMAIL_RE.match(email):
                return self._send(200, '{"mustChange":false}', 'application/json')
            result = must_change(email)
            self._send(200, json.dumps({'mustChange': result}), 'application/json')
        else:
            self._send(404, '<h1>404</h1>')

    def do_POST(self):
        if self.path != '/pw/api/change':
            return self._send(404, '{"ok":false,"error":"server"}', 'application/json')
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            email = str(body.get('email', '')).strip().lower()
            current = str(body.get('currentPassword', ''))
            new = str(body.get('newPassword', ''))
        except Exception:
            return self._send(400, '{"ok":false,"error":"server"}', 'application/json')

        if not EMAIL_RE.match(email):
            return self._send(400, '{"ok":false,"error":"current"}', 'application/json')
        if len(new) < 8 or len(new) > 128:
            return self._send(400, '{"ok":false,"error":"invalid"}', 'application/json')

        with _fail_lock:
            cnt, until = _fail.get(email, [0, 0])
            if time.time() < until:
                return self._send(429, '{"ok":false,"error":"locked"}', 'application/json')

        result = call_librechat(email, current, new)
        if result.get('ok'):
            with _fail_lock:
                _fail.pop(email, None)
            print(f'[pw] OK   {email}', flush=True)
        else:
            err = result.get('error', 'server')
            if err == 'current':
                with _fail_lock:
                    cnt, until = _fail.get(email, [0, 0])
                    cnt += 1
                    _fail[email] = [cnt, time.time() + LOCK_SECONDS if cnt >= MAX_FAILS else until]
            print(f'[pw] FAIL {email} ({err})', flush=True)
        self._send(200, json.dumps(result), 'application/json')

    def log_message(self, fmt, *args):
        pass  # 静默访问日志，只保留 do_POST 里的结果日志


def ensure_node_script(container):
    """把 node 校验脚本放进容器 /tmp（幂等）。"""
    import tempfile, os
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(NODE_JS)
        tmp = f.name
    subprocess.run(['rm', '-f', '/tmp/pw_change.node.js'], check=True)
    subprocess.run(['cp', tmp, '/tmp/pw_change.node.js'], check=True)
    subprocess.run(['chmod', '644', '/tmp/pw_change.node.js'], check=True)  # 容器内 node 以 uid1000 运行，须可读
    os.unlink(tmp)
    subprocess.run(['docker', 'cp', '/tmp/pw_change.node.js', f'{container}:/tmp/'], check=True)


def main():
    global _container, _mongo, _db
    ap = argparse.ArgumentParser()
    ap.add_argument('--dev', action='store_true')
    ap.add_argument('--prod', action='store_true')
    args = ap.parse_args()
    if args.dev == args.prod:
        sys.exit('必须且只能指定 --dev 或 --prod 其一')
    cfg = CONTAINERS['dev' if args.dev else 'prod']
    _container, _mongo, _db, port = cfg['api'], cfg['mongo'], cfg['db'], cfg['port']
    ensure_node_script(_container)
    print(f'[pw] pwpanel up on 127.0.0.1:{port} (api={_container}, mongo={_mongo}/{_db})', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    main()
