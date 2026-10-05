#!/usr/bin/env python3
"""Patch v8: ZCode 风格活动时间线（替代 v7，基于 v6+green_check 状态打）。

输出格式：
- 工具事件 = 紧凑单行「emoji 标签…」，完成时 ✓ 接在行尾（长标签截断 66 字符）；
- 模型旁白关闭 think 块后，若又来工具事件，重新开一个 <think> 块（v7 只包第一段，
  后续活动行全部漏成正文深色大段文字，这是本次要修的核心问题）；
- 孤立的 completed/error 事件（前一行已被新工具行顶掉）直接丢弃，不再输出孤立 ✓ 行；
- think 块关闭前写入「— 思考了 N 秒 —」标记，前端补丁（patch_think_ui_v2.py）据此把
  标题改成「思考 · 持續了 N 秒」并在结束后自动收起。

标记 PATCH-THINK-V8（含 v3/v4/v5/v6 全部逻辑）。在服务器上以 root 运行。
"""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'PATCH-THINK-V8' in src:
    print('[v8 already applied]')
    sys.exit(0)

# ---- A. running/completed 输出：紧凑单行 + 旁白后重新开块 + 丢弃孤立事件 ----
anchor_a = '''                    if _status == "running":
                        _head = ""
                        if not _emit._act:
                            _head = "<think>\\n"
                            _emit._act = True
                        _txt = _head + "> %s %s…\\n" % (
                            _p.get("emoji", "⚙️"),
                            _mask(_p.get("label") or _p.get("tool", "")),
                        )
                    elif _status == "completed":
                        _txt = " ✅\\n"
                    else:
                        _txt = ""'''

replacement_a = '''                    if not hasattr(_emit, "_act_t0"):
                        _emit._act_t0 = None

                    def _v8short(s):
                        if not s:
                            return s
                        s = " ".join(str(s).split())
                        if len(s) > 66:
                            s = s[:63] + "…"
                        return s

                    if _status == "running":
                        if not _emit._act:
                            _txt = "<think>\\n"
                            _emit._act = True
                            _emit._act_t0 = time.monotonic()
                            _emit._line_open = False
                        elif getattr(_emit, "_act_done", False):
                            _txt = "\\n\\n<think>\\n"
                            _emit._act_done = False
                            _emit._act_t0 = time.monotonic()
                            _emit._line_open = False
                        elif getattr(_emit, "_line_open", False):
                            _txt = "\\n\\n"
                        else:
                            _txt = ""
                        _txt += "%s %s…" % (
                            _p.get("emoji", "⚙️"),
                            _v8short(_mask(_p.get("label") or _p.get("tool", ""))),
                        )
                        _emit._line_open = True
                    elif _status == "completed":
                        if getattr(_emit, "_line_open", False):
                            _txt = " ✓\\n\\n"
                            _emit._line_open = False
                        else:
                            _txt = ""
                    elif _status in ("error", "failed", "cancelled", "canceled"):
                        if getattr(_emit, "_line_open", False):
                            _txt = " ✗\\n\\n"
                            _emit._line_open = False
                        else:
                            _txt = ""
                    else:
                        _txt = ""'''

assert anchor_a in src, 'anchor A (v6 running/completed) not found — need v6+green_check state'
src = src.replace(anchor_a, replacement_a, 1)

# ---- B. 回答开始关闭 think 块时：先补行尾，再写时长标记 ----
anchor_b = '''                    _think_close = ""
                    if _emit._act and not _emit._act_done:
                        _think_close = "</think>\\n"
                        _emit._act_done = True'''

replacement_b = '''                    _think_close = ""
                    if _emit._act and not _emit._act_done:
                        _v8tail = ""
                        if getattr(_emit, "_line_open", False):
                            _v8tail += "\\n\\n"
                            _emit._line_open = False
                        try:
                            _v8dur = max(1, int(time.monotonic() - (_emit._act_t0 or time.monotonic())))
                        except Exception:
                            _v8dur = 0
                        if _v8dur:
                            _v8tail += "— 思考了 %d 秒 —" % _v8dur
                        _think_close = _v8tail + "\\n</think>\\n"
                        _emit._act_done = True'''

assert anchor_b in src, 'anchor B (think close) not found'
src = src.replace(anchor_b, replacement_b, 1)

# ---- C. 流结束兜底：同样写入时长标记 ----
anchor_c = '''            if getattr(_emit, "_act", False) and not getattr(_emit, "_act_done", True):
                _emit._act_done = True
                _close_chunk = {
                    "id": completion_id, "object": "chat.completion.chunk",
                    "created": created, "model": model,
                    "choices": [{"index": 0, "delta": {"content": "</think>\\n"}, "finish_reason": None}],
                }
                await response.write(f"data: {json.dumps(_close_chunk)}\\n\\n".encode())'''

replacement_c = '''            if getattr(_emit, "_act", False) and not getattr(_emit, "_act_done", True):
                _emit._act_done = True
                _v8tail = ""
                if getattr(_emit, "_line_open", False):
                    _v8tail += "\\n\\n"
                try:
                    _v8dur = max(1, int(time.monotonic() - (getattr(_emit, "_act_t0", None) or time.monotonic())))
                except Exception:
                    _v8dur = 0
                if _v8dur:
                    _v8tail += "— 思考了 %d 秒 —" % _v8dur
                _close_chunk = {
                    "id": completion_id, "object": "chat.completion.chunk",
                    "created": created, "model": model,
                    "choices": [{"index": 0, "delta": {"content": _v8tail + "\\n</think>\\n"}, "finish_reason": None}],
                }
                await response.write(f"data: {json.dumps(_close_chunk)}\\n\\n".encode())'''

assert anchor_c in src, 'anchor C (flush) not found'
src = src.replace(anchor_c, replacement_c, 1)

src = src.replace('PATCH-MEDIA-V6', 'PATCH-MEDIA-V8')
src = src.replace('PATCH-THINK-V6', 'PATCH-THINK-V8')
shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src)

data = open(P, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes present!'
print('[v8 patched, file clean]')
