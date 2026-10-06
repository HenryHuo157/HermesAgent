#!/usr/bin/env python3
"""Add model.supports_vision: true to Hermes config.yaml (backup first, idempotent)."""
import re, shutil, os

P = '/home/admin/.hermes/config.yaml'
BAK = P + '.bak-20261005-vision'

s = open(P, encoding='utf-8').read()
if 'supports_vision' in s:
    print('already present, nothing to do')
    raise SystemExit(0)

if not os.path.exists(BAK):
    shutil.copyfile(P, BAK)
    print(f'[backup] {BAK}')

m = re.search(r'(?m)^model:\n(  default:[^\n]*\n)', s)
assert m, 'model block anchor not found'
s = s[:m.end(1)] + '  supports_vision: true\n' + s[m.end(1):]
open(P, 'w', encoding='utf-8').write(s)
print('[edit] supports_vision: true inserted under model:')
