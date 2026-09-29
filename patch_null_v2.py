#!/usr/bin/env python3
"""Patch v2: _read_referenced_script must survive NUL-byte paths (ValueError)."""
import shutil, sys, datetime

LG = '/home/admin/.hermes/hermes-agent/cron/lifecycle_guard.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(LG, encoding='utf-8').read()
if 'PATCH-NUL-V2' in src:
    print('[v2 already applied]')
    sys.exit(0)

old = """    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None, False"""
new = """    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except (OSError, ValueError):  # PATCH-NUL-V2: ValueError = NUL byte in path
        return None, False"""

assert old in src, 'anchor not found'
shutil.copy(LG, LG + '.bak.' + stamp)
open(LG, 'w', encoding='utf-8').write(src.replace(old, new, 1))

data = open(LG, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes in file!'
print('[v2 patched, file clean]')
