#!/usr/bin/env python3
"""Patch terminal_tool + lifecycle_guard to sanitize NUL bytes in commands."""
import shutil, sys, datetime

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
TT = '/home/admin/.hermes/hermes-agent/tools/terminal_tool.py'
LG = '/home/admin/.hermes/hermes-agent/cron/lifecycle_guard.py'

NULCHECK = 'if command and "\\x00" in command:\n        command = command.replace("\\x00", "")'

# ---- patch 1: terminal_tool function entry ----
src = open(TT, encoding='utf-8').read()
if 'PATCH-NUL-2026' in src:
    print('[1] already patched')
else:
    marker = ') -> str:'
    idx = src.find(marker, src.find('def terminal_tool('))
    assert idx > 0, 'signature not found'
    nl = src.find('\n', idx)
    inject = ('\n    # PATCH-NUL-2026: strip NUL bytes leaked from binary context\n    '
              + NULCHECK + '\n')
    shutil.copy(TT, TT + '.bak.' + stamp)
    open(TT, 'w', encoding='utf-8').write(src[:nl] + inject + src[nl:])
    print('[1] terminal_tool patched')

# ---- patch 2: lifecycle_guard entry ----
src = open(LG, encoding='utf-8').read()
if 'PATCH-NUL-2026' in src:
    print('[2] already patched')
else:
    anchor = '    """Detect lifecycle/submit commands, including bounded nested scripts."""\n    return _contains_unsafe_gateway_action('
    repl = ('    """Detect lifecycle/submit commands, including bounded nested scripts."""\n'
            '    # PATCH-NUL-2026: strip NUL bytes before path extraction\n    '
            + NULCHECK + '\n    return _contains_unsafe_gateway_action(')
    assert anchor in src, 'anchor not found'
    shutil.copy(LG, LG + '.bak.' + stamp)
    open(LG, 'w', encoding='utf-8').write(src.replace(anchor, repl, 1))
    print('[2] lifecycle_guard patched')

# ---- verify: files contain no actual NUL bytes ----
for p in (TT, LG):
    data = open(p, 'rb').read()
    n = data.count(b'\x00')
    print(f'[{p.split("/")[-1]}] actual NUL bytes: {n}')
    assert n == 0, 'REAL NUL BYTES PRESENT — restore backup!'
print('[done]')
