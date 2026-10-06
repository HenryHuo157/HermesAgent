#!/usr/bin/env python3
"""Local test driver for lc_custom.js (uses LC_INDEX_PATH override)."""
import re, subprocess, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TMP = r'X:\Henry Huo\Hermes Agents\lc-patches\tmp'
JS  = r'X:\Henry Huo\Hermes Agents\lc-patches\lc_custom.js'
SNAP = r'X:\Henry Huo\Hermes Agents\lc-patches\archive\live_index_snapshot_2026-10-05.html'

MARKS = ['hide-badges-2026', 'tasks-panel-2026', 'think-ui-2026b', 'skills-picker-v7', 'usage-link-2026c']

html = open(SNAP, encoding='utf-8').read()

# build vanilla: strip the 5 live blocks by exact string (bounded by next block start)
pos = {}
for mark in MARKS:
    m = re.search(r'<style>\s*/\* PATCH-MARK: ' + re.escape(mark), html)
    assert m, mark
    pos[mark] = m.start()
order = sorted(MARKS, key=pos.get)
bounds = {order[i]: (pos[order[i + 1]] if i + 1 < len(order) else len(html)) for i in range(len(order))}
blocks = {}
for mark in MARKS:
    start = pos[mark]
    end_style = html.find('</style>', start) + 8
    end_script = html.find('</script>', start)
    end = end_script + 9 if 0 < end_script < bounds[mark] else end_style
    blk = html[start:end]
    assert html.count(blk) == 1, mark
    blocks[mark] = blk
vanilla = html
for mark in MARKS:
    vanilla = vanilla.replace(blocks[mark], '')
vanilla = vanilla.replace('\n\n</head>', '\n</head>').replace('\n\n</body>', '\n</body>')
open(os.path.join(TMP, 'vanilla.html'), 'w', encoding='utf-8', newline='\n').write(vanilla)
print(f'vanilla built: {len(vanilla)} chars (snapshot {len(html)})')

def run(idx, expect_in_out=None):
    env = dict(os.environ, LC_INDEX_PATH=idx)
    r = subprocess.run(['node', JS], capture_output=True, text=True, env=env,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    if expect_in_out and expect_in_out not in out:
        print(f'  FAIL: expected {expect_in_out!r} in output:\n{out}')
        sys.exit(1)
    print(f'  node exit={r.returncode} out={out.strip()[:100]}')
    return out

def check(idx, cond, label):
    s = open(idx, encoding='utf-8').read()
    if not cond(s):
        print(f'  FAIL: {label}')
        sys.exit(1)
    print(f'  ok: {label}')

def marks_once(s):
    """every section present; per-mark count must equal its count in the pristine snapshot
    (think-ui's mark string legitimately appears twice: style comment + script comment)"""
    return all(s.count('PATCH-MARK: ' + m) == html.count('PATCH-MARK: ' + m) for m in MARKS)

print('\n[T1] legacy-format patched snapshot -> normalize once, then fast path')
t1 = os.path.join(TMP, 't1.html')
open(t1, 'w', encoding='utf-8', newline='\n').write(html)
run(t1, 'injected 5 sections')   # first run: reformat into sentinels
check(t1, marks_once, 'all marks present with expected counts')
snapshot_after = open(t1, encoding='utf-8').read()
run(t1, 'already applied')       # second run: fast path
check(t1, lambda s: s == snapshot_after, 'file unchanged')

print('\n[T2] vanilla -> inject 5 sections')
t2 = os.path.join(TMP, 't2.html')
open(t2, 'w', encoding='utf-8', newline='\n').write(vanilla)
run(t2, 'injected 5 sections')
check(t2, marks_once, 'all 5 marks exactly once')
check(t2, lambda s: 'lc-custom:head:v1' in s and 'lc-custom:body:v1' in s, 'sentinels present')
hi = t2 and open(t2, encoding='utf-8').read()
check(t2, lambda s: 0 <= s.find('lc-custom:head:v1 START') < s.find('lc-custom:head:v1 END') < s.find('</head>'), 'head chunk inside <head>')
check(t2, lambda s: 0 <= s.find('lc-custom:body:v1 START') < s.find('lc-custom:body:v1 END') < s.find('</body>'), 'body chunk inside <body>')

print('\n[T3] rerun t2 -> idempotent')
before = open(t2, encoding='utf-8').read()
run(t2, 'already applied')
check(t2, lambda s: s == before, 'file unchanged')

print('\n[T4] vanilla + legacy blocks -> legacy stripped, sections injected')
t4 = os.path.join(TMP, 't4.html')
legged = vanilla.replace('</head>',
    '<style>\n/* PATCH-MARK: skills-picker-v6 — old */\n#lc-skillbtn{old:1;}\n</style>\n<script>/* old picker */\n(function(){})();\n</script>\n'
    '<style>/* PATCH-MARK: working-verbs-2026 — old */\n.wv{display:none;}\n</style>\n'
    '<script>/* PATCH-MARK: working-verbs-2026 — old js */\nconsole.log(1);\n</script>\n</head>', 1)
open(t4, 'w', encoding='utf-8', newline='\n').write(legged)
run(t4, 'injected 5 sections')
check(t4, marks_once, 'all 5 marks exactly once')
check(t4, lambda s: 'skills-picker-v6' not in s and 'working-verbs-2026' not in s, 'legacy blocks removed')

print('\nALL TESTS PASSED')
