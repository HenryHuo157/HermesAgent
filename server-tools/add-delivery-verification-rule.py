#!/usr/bin/env python3
"""add-delivery-verification-rule.py — SOUL.md 增加「交付验证」硬规则（方案 A）
生产（/srv/hermes-share）与 Dev（/srv/hermes-share-dev）同步注入，幂等，改前自动备份。"""
import shutil, sys, datetime

STAMP = '20261007-delivery'
RULE = ('\nDelivery verification (mandatory): before outputting ANY /m/ link or MEDIA: tag, the target '
        'file must physically exist inside {share}/. If the file is still in your working folder '
        '(e.g. {home}/...), first `cp` it into {share}/, then `ls -la` the copied file to confirm — '
        'only then hand out the link. Never claim 已放入共用資料夾 unless the copy + ls actually '
        'happened; an unverified link is a broken deliverable.\n')
ANCHOR = 'Never put MEDIA: paths under'

TARGETS = [
    ('/home/admin/.hermes/SOUL.md', '/srv/hermes-share', '/home/admin'),
    ('/home/dev/.hermes/SOUL.md', '/srv/hermes-share-dev', '/home/dev'),
]

for path, share, home in TARGETS:
    try:
        src = open(path, encoding='utf-8').read()
    except FileNotFoundError:
        print(f'[skip] {path} 不存在')
        continue
    if 'Delivery verification (mandatory)' in src:
        print(f'[ok] {path} 已有该规则，跳过')
        continue
    idx = src.find(ANCHOR)
    if idx < 0:
        print(f'[fail] {path} 找不到锚点行，未改动'); continue
    eol = src.find('\n', idx)
    if eol < 0: eol = len(src)
    bak = f'{path}.bak-{STAMP}'
    shutil.copy(path, bak)
    out = src[:eol] + RULE.format(share=share, home=home) + src[eol:]
    open(path, 'w', encoding='utf-8').write(out)
    print(f'[done] {path} 已注入规则（备份 {bak}）')
