#!/usr/bin/env python3
"""Add lc-patches volume mount + startup patch hook to /opt/lc-run/docker-compose.yml.
Backs up the original first. Idempotent."""
import shutil, sys

CF = '/opt/lc-run/docker-compose.yml'
BAK = CF + '.bak-20261005'
MOUNT = '      - /opt/lc-patches:/opt/lc-patches:ro'
CMD = '    command: sh -c "node /opt/lc-patches/lc_custom.js || true; exec npm run backend"'

s = open(CF, encoding='utf-8').read()
orig = s

import os
if not os.path.exists(BAK):
    shutil.copyfile(CF, BAK)
    print(f'[backup] {BAK}')

if MOUNT not in s:
    anchor = '      - /opt/librechat/images:/app/client/public/images\n'
    assert anchor in s, 'images volume anchor not found'
    s = s.replace(anchor, anchor + MOUNT + '\n', 1)
    print('[edit] volume mount added')

if 'lc_custom.js' not in s:
    anchor2 = '    container_name: librechat-api\n'
    assert anchor2 in s, 'api container_name anchor not found'
    s = s.replace(anchor2, anchor2 + CMD + '\n', 1)
    print('[edit] startup patch command added')

if s == orig:
    print('[edit] nothing to change (already configured)')
else:
    open(CF, 'w', encoding='utf-8', newline='\n').write(s)
    print('[edit] compose file written')
