#!/usr/bin/env python3
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
snap = open(r'X:\Henry Huo\Hermes Agents\lc-patches\archive\live_index_snapshot_2026-10-05.html', encoding='utf-8').read()
t2 = open(r'X:\Henry Huo\Hermes Agents\lc-patches\tmp\t2.html', encoding='utf-8').read()
marks = ['hide-badges-2026','tasks-panel-2026','think-ui-2026b','skills-picker-v7','usage-link-2026c']

pos, order = {}, []
for mk in marks:
    m = re.search(r'<style>\s*/\* PATCH-MARK: ' + re.escape(mk), snap)
    pos[mk] = m.start(); order.append(mk)
order.sort(key=pos.get)
bounds = {order[i]: (pos[order[i+1]] if i+1 < len(order) else len(snap)) for i in range(len(order))}

ok = True
for mk in marks:
    start = pos[mk]
    end = snap.find('</style>', start) + 8
    es = snap.find('</script>', start)
    if 0 < es < bounds[mk]:
        end = es + 9
    blk = snap[start:end]
    n = t2.count(blk)
    print(f'{mk:22s} len={len(blk):5d} verbatim in patched output: {n}')
    ok = ok and n >= 1
sys.exit(0 if ok else 1)
