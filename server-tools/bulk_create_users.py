#!/usr/bin/env python3
"""批量创建 LibreChat 用户：读 CSV(email,name,password)，经 librechat-api 容器内
bcryptjs 生成 hash（与 LibreChat 登录校验同构）后写入对应 mongo 库。
幂等：邮箱已存在则跳过。Dev/生产通过 --dev/--prod 选择容器，须显式 --yes 才写库。

用法:
    python bulk_create_users.py users.csv --dev --yes
    python bulk_create_users.py users.csv --prod --yes
CSV 格式（# 开头为注释行）: email,name,password
"""
import argparse, json, subprocess, sys, tempfile, csv
from pathlib import Path

CONTAINERS = {
    'dev': 'librechat-dev-api',
    'prod': 'librechat-api',
}

# 在 LibreChat 容器内执行：stdin 收 JSON 数组，逐个建号
NODE_JS = r"""
const mongodb = require('/app/node_modules/mongodb');
const bcrypt = require('/app/node_modules/bcryptjs');
(async () => {
  const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
  const client = new mongodb.MongoClient(process.env.MONGO_URI);
  await client.connect();
  const col = client.db().collection('users');
  const results = [];
  for (const u of input) {
    const email = String(u.email).trim().toLowerCase();
    try {
      const exists = await col.findOne({ email: email });
      if (exists) { results.push({ email: email, status: 'exists' }); continue; }
      await col.insertOne({
        name: u.name || email.split('@')[0],
        username: null,
        email: email,
        emailVerified: true,
        avatar: null,
        provider: 'local',
        role: 'USER',
        password: bcrypt.hashSync(u.password, 10),
        plugins: [],
        twoFactorEnabled: false,
        termsAccepted: true,
        termsAcceptedAt: new Date(),
        mustChangePassword: true,
        personalization: { memories: true, statefulCodeEnvironment: 'user' },
        pinnedOrder: [],
        backupCodes: [],
        refreshToken: [],
        skillStates: {},
        createdAt: new Date(),
        updatedAt: new Date(),
        __v: 0,
      });
      results.push({ email: email, status: 'created' });
    } catch (e) {
      results.push({ email: email, status: 'error', error: String(e && e.message || e) });
    }
  }
  console.log('RESULT:' + JSON.stringify(results));
  await client.close();
})().catch(e => { console.error('FATAL:' + String(e && e.message || e)); process.exit(1); });
"""


def read_csv(path):
    users = []
    for lineno, raw in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) != 3 or '@' not in parts[0]:
            sys.exit(f'CSV 第 {lineno} 行格式错误（应为 email,name,password）：{line}')
        users.append({'email': parts[0], 'name': parts[1], 'password': parts[2]})
    if not users:
        sys.exit('CSV 里没有任何用户行')
    return users


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv', help='用户清单 CSV：email,name,password')
    ap.add_argument('--dev', action='store_true', help='写入 Dev（librechat-dev-api → LibreChatDev 库）')
    ap.add_argument('--prod', action='store_true', help='写入生产（librechat-api → LibreChat 库）')
    ap.add_argument('--yes', action='store_true', help='确认执行写库')
    args = ap.parse_args()

    if args.dev == args.prod:
        sys.exit('必须且只能指定 --dev 或 --prod 其一')
    mode = 'dev' if args.dev else 'prod'
    container = CONTAINERS[mode]

    users = read_csv(args.csv)
    print(f'目标：{mode}（docker 容器 {container}，MONGO_URI 指向的库）')
    print(f'待处理 {len(users)} 个账号：')
    for u in users:
        print(f"  {u['email']}  ({u['name']})")
    if not args.yes:
        print('\n[干跑] 未写库。确认无误后加 --yes 执行。')
        return

    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(NODE_JS)
        js_path = f.name

    try:
        subprocess.run(['ssh', 'root@47.243.79.144', 'rm -f /tmp/bulk_create_users.node.js'],
                       check=True, capture_output=True)
        subprocess.run(['scp', js_path, 'root@47.243.79.144:/tmp/bulk_create_users.node.js'],
                       check=True, capture_output=True)
        subprocess.run(['ssh', 'root@47.243.79.144',
                        f'docker cp /tmp/bulk_create_users.node.js {container}:/tmp/'],
                       check=True, capture_output=True)
        payload = json.dumps(users)
        proc = subprocess.run(
            ['ssh', 'root@47.243.79.144',
             f"docker exec -i -w /app {container} node /tmp/bulk_create_users.node.js"],
            input=payload, capture_output=True, text=True, timeout=120)
        result_line = None
        for line in proc.stdout.splitlines():
            if line.startswith('RESULT:'):
                result_line = line[len('RESULT:'):]
        if result_line is None:
            print('STDOUT:', proc.stdout)
            print('STDERR:', proc.stderr)
            sys.exit(f'远端执行失败（exit={proc.returncode}），未拿到结果')
        results = json.loads(result_line)
        print('\n执行结果：')
        for r in results:
            mark = {'created': '✅ 已创建', 'exists': '⏭️ 已存在，跳过', 'error': '❌ 失败'}.get(r['status'], r['status'])
            extra = f" — {r['error']}" if r.get('error') else ''
            print(f"  {r['email']}: {mark}{extra}")
        bad = [r for r in results if r['status'] == 'error']
        sys.exit(1 if bad else 0)
    finally:
        Path(js_path).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
