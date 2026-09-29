#!/usr/bin/env python3
"""Patch v5: line-buffered MEDIA: transform in the streaming path.
Replaces the per-chunk v4 logic (which failed when tags span deltas)."""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'PATCH-MEDIA-V5' in src:
    print('[v5 already applied]')
    sys.exit(0)

# ---- 1. replace the v4 transform block (its `if isinstance...MEDIA:` line ..
#        just before content_chunk) with line-buffered logic ----
i = src.find('                    if isinstance(_item, str) and "MEDIA:" in _item:')
assert i > 0, 'v4 if-line not found'
j = src.find('                    content_chunk = {', i)
assert j > i, 'content_chunk anchor not found'

new_logic = r'''                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""
                    if isinstance(item, str):
                        _buf = _emit._lbuf + item
                        if "MEDIA" in _buf:
                            _nl = _buf.rfind("\n")
                            _head, _tail = _buf[:_nl + 1], _buf[_nl + 1:]
                            _item = _media_transform(_head)
                            _i = _tail.rfind("MEDIA")
                            if _i == -1:
                                _item += _media_transform(_tail)
                                _tail = ""
                            else:
                                _item += _tail[:_i]
                                _tail = _tail[_i:]
                            _emit._lbuf = _tail
                        else:
                            _emit._lbuf = ""
                            _item = item
                        if _item == "" and _buf != "":
                            return time.monotonic()
                    else:
                        _item = item
'''

src = src[:i] + new_logic + src[j:]

# ---- 2. define _media_transform just before the streaming loop ----
anchor2 = '            # Stream content chunks as they arrive from the agent'
transform = r'''            def _media_transform(s):
                if not s:
                    return s
                import re as _re, shutil as _shutil, os as _os, urllib.parse as _up

                def _repl(m):
                    p = m.group(1)
                    try:
                        if _os.path.isfile(p) and _os.path.dirname(p) != "/srv/hermes-share":
                            _shutil.copy(p, "/srv/hermes-share/")
                    except Exception:
                        pass
                    _name = _os.path.basename(p)
                    _enc = _up.quote(_name)
                    return "![生成图片](https://47.243.79.144/m/%s)" % _enc

                s = _re.sub(r"MEDIA:\s*[\"']?([^\s\"'`]+?\.(?:png|jpe?g|gif|webp|bmp))", _repl, s)
                s = s.replace("MEDIA:", "")
                return s

'''
k = src.find(anchor2)
assert k > 0, 'stream loop anchor not found'
src = src[:k] + transform + src[k:]

# ---- 3. flush remaining buffer after the stream loop ends ----
anchor3 = '            # Get usage from completed agent.'
flush = r'''            if getattr(_emit, "_lbuf", ""):
                _rest = _media_transform(_emit._lbuf)
                _emit._lbuf = ""
                if _rest:
                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": _rest}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\n\n".encode())

'''
k = src.find(anchor3)
assert k > 0, 'usage anchor not found'
src = src[:k] + flush + src[k:]

src = src.replace('PATCH-MEDIA-2026', 'PATCH-MEDIA-V5')
shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src)

data = open(P, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes present!'
print('[v5 patched, file clean]')
