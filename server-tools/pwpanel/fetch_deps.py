#!/usr/bin/env python3
"""自动补齐 fal 依赖 wheel:循环 pip --no-index 安装 → 解析缺失包+约束 →
从镜像 simple 页面抓满足约束的 wheel → 下载到 /tmp/falwheels,直到安装成功。
(镜像限流时自动退避重试,并可用第二镜像)"""
import re, subprocess, sys, time, urllib.request

MIRRORS = ['https://mirrors.aliyun.com/pypi', 'https://pypi.org']
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/126.0.0.0 Safari/537.36'}
VENV_PY = '/home/admin/.hermes/hermes-agent/venv/bin/python'
WHEEL_DIR = '/tmp/falwheels'

def http_get(url, binary=False, timeout=90):
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            data = urllib.request.urlopen(req, timeout=timeout).read()
            return data if binary else data.decode('utf-8', 'replace')
        except Exception as e:
            last = e
            sys.stdout.write(f'    retry {attempt+1} ({e})\n'); sys.stdout.flush()
            time.sleep(15 * (attempt + 1))
    raise last

def spec_match(version, spec_str):
    ok = True
    for part in spec_str.split(','):
        part = part.strip()
        m = re.match(r'(>=|<=|>|<|==|~=)\s*([\d.]+)', part)
        if not m:
            continue
        op, ver = m.group(1), m.group(2)
        a = [int(x) for x in re.split(r'[.\-]', version) if x.isdigit()]
        b = [int(x) for x in ver.split('.')]
        n = max(len(a), len(b))
        a += [0] * (n - len(a)); b += [0] * (n - len(b))
        if op == '>=' and not a >= b: ok = False
        if op == '<=' and not a <= b: ok = False
        if op == '>' and not a > b: ok = False
        if op == '<' and not a < b: ok = False
        if op == '==' and a != b: ok = False
        if op == '~=' and not (a[:len(b)-1] == b[:len(b)-1] and a >= b): ok = False
    return ok

def fetch_wheel(name, spec_str, mirror):
    base = f'{mirror}/{name}/'
    html = http_get(base)
    cands = []
    for m in re.finditer(r'href="([^"]+)"[^>]*>([^<]+)</a>', html):
        href, fname = m.group(1), m.group(2).strip()
        vm = re.match(re.escape(name.replace('-', '_')) + r'-(\d[\w.]*)-(py3-none-any|py2\.py3-none-any|cp311-cp311-manylinux[_0-9a-z]*_x86_64)\.whl$', fname, re.I)
        if not vm:
            continue
        ver = vm.group(1)
        if name.lower() == 'isolate' and ver.startswith('0.9'):
            continue
        if spec_match(ver, spec_str):
            cands.append((ver, fname, href))
    if not cands:
        return None
    cands.sort(key=lambda x: [int(p) if p.isdigit() else 0 for p in re.split(r'[.\-]', x[0])])
    ver, fname, href = cands[-1]
    dl = mirror + '/' + href.lstrip('./')
    if '#' in dl:
        dl = dl.split('#')[0]
    sys.stdout.write(f'  fetch {fname} ({ver})\n  url: {dl}\n'); sys.stdout.flush()
    data = http_get(dl, binary=True)
    if data[:2] != b'PK':
        raise RuntimeError(f'{fname} not a wheel')
    open(WHEEL_DIR + '/' + fname, 'wb').write(data)
    return fname

def main():
    for rnd in range(1, 15):
        r = subprocess.run([VENV_PY, '-m', 'pip', 'install', '-q', '--no-index',
                            '--find-links', WHEEL_DIR, 'fal'],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(f'INSTALL OK (round {rnd})')
            break
        err = r.stderr or r.stdout
        mm = re.search(r'satisfies the requirement ([^\s(]+)', err)
        if not mm:
            print('install failed, unparsed:'); print(err[-600:]); return 1
        pkg = mm.group(1)
        name = re.split(r'[<>=~,!\[\s]', pkg)[0]
        spec = re.sub(r';.*', '', pkg[len(name):]).strip()
        print(f'round {rnd}: missing {name} {spec}')
        done = False
        for mirror in MIRRORS:
            try:
                if fetch_wheel(name, spec, mirror) is not None:
                    done = True; break
                print(f'  {mirror}: no matching wheel')
            except Exception as e:
                print(f'  {mirror}: {e}')
        if not done:
            print('all mirrors exhausted'); return 1
    r = subprocess.run([VENV_PY, '-c', 'import fal; print("FINAL: fal import OK")'], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-300:])
    return 0

sys.exit(main())
