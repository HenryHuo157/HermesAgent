#!/usr/bin/env python3
"""Patch v4: in streaming, rewrite MEDIA:<path> in content into inline markdown
images/links served from /m/ (auto-copying files into the share dir)."""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'PATCH-MEDIA-2026' in src:
    print('[v4 already applied]')
    sys.exit(0)

old = '''                else:
                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": item}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\\n\\n".encode())'''

new = '''                else:
                    _item = item
                    if isinstance(_item, str) and "MEDIA:" in _item:
                        # PATCH-MEDIA-2026: turn internal MEDIA:<path> tags into
                        # inline markdown (images render, files get /m/ links);
                        # non-share paths are copied into the share dir first.
                        import re as _re, shutil as _shutil, os as _os, urllib.parse as _up

                        def _media_repl(m):
                            p = m.group(1)
                            try:
                                if _os.path.isfile(p) and _os.path.dirname(p) != "/srv/hermes-share":
                                    _shutil.copy(p, "/srv/hermes-share/")
                            except Exception:
                                pass
                            _name = _os.path.basename(p)
                            _ext = _name.rsplit(".", 1)[-1].lower()
                            _enc = _up.quote(_name)
                            if _ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
                                return "![生成图片](https://47.243.79.144/m/%s)" % _enc
                            return "📥 [下载 %s](https://47.243.79.144/m/%s)" % (_name, _enc)

                        _item = _re.sub(
                            r"MEDIA:\\s*[\\\"']?([^\\s\\\"'`]+?\\.(?:png|jpe?g|gif|webp|bmp|pdf|zip|xlsx?|docx?))",
                            _media_repl, _item,
                        )
                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": _item}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\\n\\n".encode())'''

assert old in src, 'else-branch anchor not found'
shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src.replace(old, new, 1))

data = open(P, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes present!'
print('[v4 patched, file clean]')
