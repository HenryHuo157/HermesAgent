#!/usr/bin/env python3
"""Patch v3: mirror tool progress events into the chat-completions content stream."""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'PATCH-ACTIVITY-2026' in src:
    print('[v3 already applied]')
    sys.exit(0)

anchor = '''                if isinstance(item, tuple) and len(item) == 2 and item[0] == "__tool_progress__":
                    event_data = json.dumps(item[1])
                    await response.write(
                        f"event: hermes.tool.progress\\ndata: {event_data}\\n\\n".encode()
                    )'''

replacement = '''                if isinstance(item, tuple) and len(item) == 2 and item[0] == "__tool_progress__":
                    event_data = json.dumps(item[1])
                    await response.write(
                        f"event: hermes.tool.progress\\ndata: {event_data}\\n\\n".encode()
                    )
                    # PATCH-ACTIVITY-2026: mirror tool events into the content
                    # stream so plain OpenAI-compatible frontends render a live
                    # activity timeline without understanding custom SSE events.
                    _p = item[1]
                    _status = _p.get("status")
                    if _status == "running":
                        _txt = "\\n> %s %s…\\n" % (
                            _p.get("emoji", "\\u2699\\ufe0f"),
                            (_p.get("label") or _p.get("tool", "")),
                        )
                    elif _status == "completed":
                        _txt = " \\u2713\\n"
                    else:
                        _txt = ""
                    if _txt:
                        _chunk = {
                            "id": completion_id, "object": "chat.completion.chunk",
                            "created": created, "model": model,
                            "choices": [{"index": 0, "delta": {"content": _txt}, "finish_reason": None}],
                        }
                        await response.write(f"data: {json.dumps(_chunk)}\\n\\n".encode())'''

assert anchor in src, 'consumer anchor not found'
shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src.replace(anchor, replacement, 1))

data = open(P, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes present!'
print('[v3 patched, file clean]')
