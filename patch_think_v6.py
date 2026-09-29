#!/usr/bin/env python3
"""Patch v6: wrap mirrored tool activity in <think> blocks (native collapsible
thinking UI in LibreChat) + mask secrets in activity labels."""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'PATCH-THINK-V6' in src:
    print('[v6 already applied]')
    sys.exit(0)

# ---- A. replace v3 mirror logic with think-wrapped + masked version ----
anchor_a = '''                    if _status == "running":
                        _txt = "\\n> %s %s…\\n" % (
                            _p.get("emoji", "\\u2699\\ufe0f"),
                            (_p.get("label") or _p.get("tool", "")),
                        )
                    elif _status == "completed":
                        _txt = " \\u2713\\n"
                    else:
                        _txt = ""'''

replacement_a = '''                    if not hasattr(_emit, "_act"):
                        _emit._act = False
                        _emit._act_done = False
                    import re as _v3re

                    def _mask(s):
                        if not s:
                            return s
                        s = _v3re.sub(r"(?i)\\b(authorization|key|bearer|token)\\b[=: ]+\\S+", "[已隐藏]", s)
                        s = _v3re.sub(r"\\b[0-9a-fA-F]{32,}\\b", "[已隐藏]", s)
                        return s

                    if _status == "running":
                        _head = ""
                        if not _emit._act:
                            _head = "<think>\\n"
                            _emit._act = True
                        _txt = _head + "> %s %s…\\n" % (
                            _p.get("emoji", "⚙️"),
                            _mask(_p.get("label") or _p.get("tool", "")),
                        )
                    elif _status == "completed":
                        _txt = " ✓\\n"
                    else:
                        _txt = ""'''

assert anchor_a in src, 'anchor A (v3 mirror) not found'
src = src.replace(anchor_a, replacement_a, 1)

# ---- B. content path: close the think block when the answer starts ----
anchor_b = '''                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""
                    if isinstance(item, str):'''
replacement_b = '''                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""
                    if not hasattr(_emit, "_act"):
                        _emit._act = False
                        _emit._act_done = False
                    _think_close = ""
                    if _emit._act and not _emit._act_done:
                        _think_close = "</think>\\n"
                        _emit._act_done = True
                    if isinstance(item, str):'''
assert anchor_b in src, 'anchor B (v5 lbuf init) not found'
src = src.replace(anchor_b, replacement_b, 1)

# ---- B2. early-return path must still emit the closing tag ----
anchor_b2 = '''                        if _item == "" and _buf != "":
                            return time.monotonic()'''
replacement_b2 = '''                        if _item == "" and _buf != "":
                            _item = _think_close
                            if _item == "":
                                return time.monotonic()
                        elif _think_close:
                            _item = _think_close + _item'''
assert anchor_b2 in src, 'anchor B2 (early return) not found'
src = src.replace(anchor_b2, replacement_b2, 1)

# ---- B3. normal path: prepend closing tag ----
anchor_b3 = '''                        else:
                            _emit._lbuf = ""
                            _item = item'''
replacement_b3 = '''                        else:
                            _emit._lbuf = ""
                            _item = _think_close + item'''
assert anchor_b3 in src, 'anchor B3 (normal path) not found'
src = src.replace(anchor_b3, replacement_b3, 1)

# ---- C. flush at stream end: close any open think block ----
anchor_c = '''            if getattr(_emit, "_lbuf", ""):'''
replacement_c = '''            if getattr(_emit, "_act", False) and not getattr(_emit, "_act_done", True):
                _emit._act_done = True
                _close_chunk = {
                    "id": completion_id, "object": "chat.completion.chunk",
                    "created": created, "model": model,
                    "choices": [{"index": 0, "delta": {"content": "</think>\\n"}, "finish_reason": None}],
                }
                await response.write(f"data: {json.dumps(_close_chunk)}\\n\\n".encode())
            if getattr(_emit, "_lbuf", ""):'''
assert anchor_c in src, 'anchor C (flush) not found'
src = src.replace(anchor_c, replacement_c, 1)

src = src.replace('PATCH-MEDIA-V5', 'PATCH-MEDIA-V6')
shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src)

data = open(P, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes present!'
print('[v6 patched, file clean]')
