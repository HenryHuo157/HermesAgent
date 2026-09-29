#!/usr/bin/env python3
"""Per-user scheduled-task panel backend: bridges LibreChat users -> hermes cron."""
import json, os, re, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
REG = '/opt/taskspanel/tasks.json'
RESULTS_DIR = '/srv/hermes-share/.task-results'
HERMES = '/home/admin/.local/bin/hermes'
AUTH_URL = 'http://127.0.0.1:3080/api/user/me'
CRON_RE = re.compile(r'^[\d*,\-/\s]{5,25}$')

os.makedirs(RESULTS_DIR, exist_ok=True)
os.chmod(RESULTS_DIR, 0o755)
try:
    os.chown(RESULTS_DIR, 1000, 1000)
except OSError:
    pass

_lock = threading.Lock()
_tokcache = {}  # token -> (user, ts)


def load_reg():
    try:
        return json.load(open(REG, encoding='utf-8'))
    except Exception:
        return {}


def save_reg(d):
    tmp = REG + '.tmp'
    json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, REG)


def run_hermes(args):
    p = subprocess.run(['sudo', '-u', 'admin', '-H', HERMES, 'cron'] + args,
                       capture_output=True, text=True, timeout=120)
    return p.stdout + p.stderr


def auth_user(token):
    now = time.time()
    hit = _tokcache.get(token)
    if hit and now - hit[1] < 300:
        return hit[0]
    req = urllib.request.Request(AUTH_URL, headers={'Authorization': 'Bearer ' + token})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode())
            user = d.get('username') or (d.get('email') or 'user').split('@')[0]
            _tokcache[token] = (user, now)
            return user
    except Exception:
        return None


def cron_status_map():
    out = {}
    for line in run_hermes(['list', '--all']).splitlines():
        m = re.match(r'\s*([0-9a-f]{12})\s*\[(active|paused)\]', line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _auth(self):
        t = self.headers.get('Authorization', '').replace('Bearer ', '').strip()
        return auth_user(t) if t else None

    def do_GET(self):
        if self.path == '/tasksapi/list':
            user = self._auth()
            if not user:
                return self._json(401, {'error': '請先登入'})
            with _lock:
                reg = load_reg()
                mine = [dict(v, job_id=k) for k, v in reg.items() if v['user'] == user]
            st = cron_status_map()
            for t in mine:
                t['status'] = st.get(t['job_id'][:12], 'unknown')
            return self._json(200, {'user': user, 'tasks': mine})
        m = re.match(r'^/tasksapi/result/([0-9a-f]{8,16})$', self.path)
        if m and self._auth():
            key = m.group(1)
            try:
                txt = open(RESULTS_DIR + '/' + key + '.md', encoding='utf-8').read()[:20000]
                return self._json(200, {'result': txt})
            except Exception:
                return self._json(200, {'result': '（還沒有結果——任務還沒跑過或還在跑）'})
        return self._json(404, {'error': 'not found'})

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        try:
            body = json.loads(self.rfile.read(n).decode() or '{}')
        except Exception:
            return self._json(400, {'error': 'bad json'})
        user = self._auth()
        if not user:
            return self._json(401, {'error': '請先登入'})

        if self.path == '/tasksapi/create':
            name = str(body.get('name') or '').strip()[:40]
            cron = str(body.get('schedule') or '').strip()
            prompt = str(body.get('prompt') or '').strip()[:4000]
            if not name or not prompt or not CRON_RE.match(cron):
                return self._json(400, {'error': '名稱、時間或內容格式不正確'})
            key = os.urandom(4).hex()
            final = (prompt + '\n\n[系統] 完成後，必須用 write_file 或 terminal 將完整結果（Markdown 格式）'
                     '保存到 /srv/hermes-share/.task-results/' + key + '.md，'
                     '並在回覆中給出簡短摘要。')
            out = run_hermes(['create', '--name', '[' + user + '] ' + name, cron, final])
            m = re.search(r'Created job:\s*([0-9a-f]+)', out)
            if not m:
                return self._json(500, {'error': '創建失敗：' + out.strip()[-200:]})
            with _lock:
                reg = load_reg()
                reg[m.group(1)] = {'user': user, 'name': name, 'schedule': cron,
                                   'result_key': key, 'created': time.strftime('%F %T')}
                save_reg(reg)
            return self._json(200, {'ok': True, 'job_id': m.group(1)})

        if self.path == '/tasksapi/action':
            jid = str(body.get('job_id') or '')
            act = str(body.get('action') or '')
            if act not in ('pause', 'resume', 'run', 'remove'):
                return self._json(400, {'error': 'unknown action'})
            with _lock:
                reg = load_reg()
                meta = reg.get(jid)
            if not meta or meta['user'] != user:
                return self._json(403, {'error': '不是你的任務'})
            out = run_hermes([act, jid])
            if act == 'remove':
                with _lock:
                    reg = load_reg()
                    reg.pop(jid, None)
                    save_reg(reg)
            return self._json(200, {'ok': True, 'output': out.strip()[-150:]})

        return self._json(404, {'error': 'not found'})


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
