#!/usr/bin/env python3
"""畢卡索 监控告警（root cron 每 5 分钟）：异常发飞书群消息。

防打扰策略：只在「正常→异常」「异常→恢复」时发；持续异常每 6 小时重提醒一次。
检查项：磁盘>90%、可用内存<250MB、7 个关键容器、Hermes 进程、两个面板服务、
        网页 https 200、SearXNG 200、每日备份新鲜度（<30h）。
cron（root）：*/5 * * * * /usr/local/bin/picasso-monitor >/dev/null 2>&1
手动测试：/usr/local/bin/picasso-monitor --test   （发一条测试消息到群）
"""
import json, os, shutil, subprocess, sys, time, urllib.request

STATE_DIR = '/var/lib/picasso-monitor'
STATE_FILE = os.path.join(STATE_DIR, 'state.json')
ENV_FILE = '/home/admin/.hermes/.env'
CHAT_ID = 'oc_32b1291adb70065a3c808e3ece0a6844'   # 畢卡索 群（与每日早报同群）
RE_ALERT_HOURS = 6
BACKUP_MAX_AGE = 30 * 3600
CONTAINERS = ['librechat-api', 'librechat-mongo', 'librechat-rag_api',
              'librechat-vectordb', 'searxng', 'syncthing', 'filebrowser']
SERVICES = ['taskspanel', 'usagepanel']


def sh(cmd, timeout=20):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def run_checks():
    problems = []
    # 磁盘
    du = shutil.disk_usage('/')
    pct = round(du.used / du.total * 100)
    if pct > 90:
        problems.append(('disk', '磁盘 %d%%（阈值 90%%，剩 %.1fG）' % (pct, du.free / 2**30)))
    # 内存
    meminfo = {}
    for line in open('/proc/meminfo'):
        k, _, v = line.partition(':')
        meminfo[k.strip()] = int(v.split()[0])
    avail_mb = meminfo.get('MemAvailable', 0) // 1024
    if avail_mb < 250:
        problems.append(('mem', '可用内存仅 %dMB（阈值 250MB），有 OOM 风险' % avail_mb))
    # 容器
    for c in CONTAINERS:
        r = sh(['docker', 'inspect', '-f', '{{.State.Status}}', c])
        status = r.stdout.strip() if (r and r.returncode == 0) else 'missing'
        if status != 'running':
            problems.append(('container:' + c, '容器 %s 状态=%s' % (c, status)))
    # Hermes 进程
    r = sh(['pgrep', '-u', 'admin', '-x', 'hermes'])
    if not (r and r.returncode == 0):
        problems.append(('hermes', 'Hermes 进程不在运行（pgrep hermes 为空）'))
    # 面板 systemd 服务
    for s in SERVICES:
        r = sh(['systemctl', 'is-active', s + '.service'])
        if not (r and r.stdout.strip() == 'active'):
            problems.append(('service:' + s, '服务 %s 未 active' % s))
    # 网页入口
    r = sh(['curl', '-sk', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '15',
            'https://127.0.0.1/'])
    if not (r and r.stdout.strip().startswith('2')):
        problems.append(('web', 'LibreChat 网页无响应（HTTP %s）' % (r.stdout.strip() if r else '?')))
    # SearXNG
    r = sh(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '10',
            'http://127.0.0.1:8888/'])
    if not (r and r.stdout.strip().startswith('2')):
        problems.append(('searxng', 'SearXNG 搜索后端无响应（HTTP %s）' % (r.stdout.strip() if r else '?')))
    # 备份新鲜度
    try:
        age = time.time() - os.stat('/opt/backups/last-backup.stamp').st_mtime
        if age > BACKUP_MAX_AGE:
            problems.append(('backup', '每日备份已 %0.1f 小时未成功（阈值 30h）' % (age / 3600)))
    except OSError:
        problems.append(('backup', '找不到备份心跳文件 /opt/backups/last-backup.stamp'))
    return problems


def feishu_creds():
    app_id = app_secret = None
    for line in open(ENV_FILE, encoding='utf-8'):
        line = line.strip()
        if line.startswith('FEISHU_APP_ID='):
            app_id = line.split('=', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('FEISHU_APP_SECRET='):
            app_secret = line.split('=', 1)[1].strip().strip('"').strip("'")
    return app_id, app_secret


def feishu_send(text):
    app_id, app_secret = feishu_creds()
    if not app_id or not app_secret:
        return 'no creds'
    try:
        req = urllib.request.Request(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            data=json.dumps({'app_id': app_id, 'app_secret': app_secret}).encode(),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r:
            tok = json.loads(r.read().decode()).get('tenant_access_token')
        if not tok:
            return 'no token'
        body = json.dumps({'receive_id': CHAT_ID, 'msg_type': 'text',
                           'content': json.dumps({'text': text}, ensure_ascii=False)}).encode()
        req = urllib.request.Request(
            'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
            data=body, headers={'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + tok})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()).get('code')
    except Exception as e:
        return 'send error: %s' % e


def load_state():
    try:
        return json.load(open(STATE_FILE, encoding='utf-8'))
    except Exception:
        return {}


def save_state(st):
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(st, open(STATE_FILE + '.tmp', 'w', encoding='utf-8'))
    os.replace(STATE_FILE + '.tmp', STATE_FILE)


def notify(text):
    os.makedirs(STATE_DIR, exist_ok=True)
    code = feishu_send(text)
    with open(STATE_DIR + '/monitor.log', 'a', encoding='utf-8') as f:
        f.write(time.strftime('%F %T') + ' sent=%s %s\n' % (code, text.replace('\n', ' | ')))


def main():
    if '--test' in sys.argv:
        notify('【畢卡索監控】通道測試 ✔ 監控已上線，此條為測試消息，可忽略。')
        print('test message sent')
        return
    now = time.time()
    problems = run_checks()
    state = load_state()
    open_keys = {k for k, v in state.items() if v.get('open')}
    new_keys = {k for k, _ in problems}

    to_alert, to_recover = [], []
    for k, msg in problems:
        rec = state.get(k)
        if not rec or not rec.get('open'):
            to_alert.append(msg)
            state[k] = {'open': True, 'since': now, 'last_alert': now}
        elif now - rec.get('last_alert', 0) > RE_ALERT_HOURS * 3600:
            to_alert.append(msg + '（持續中）')
            rec['last_alert'] = now
    for k in open_keys - new_keys:
        to_recover.append(state[k].get('label', k))
        state.pop(k, None)

    if to_recover:
        notify('【畢卡索監控】✅ 已恢復：%s' % '、'.join(to_recover))
    if to_alert:
        notify('【畢卡索監控】⚠️ %d 項異常\n• %s\n（服務器 47.243.79.144）'
               % (len(to_alert), '\n• '.join(to_alert)))
    # 记录 label 便于恢复通知可读
    for k, msg in problems:
        if k in state:
            state[k]['label'] = msg.split('（')[0]
    save_state(state)


if __name__ == '__main__':
    main()
