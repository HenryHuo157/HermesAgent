#!/usr/bin/env python3
"""Patch v1 (empty-text): 空正文保护——模型偶发把最终答案整段写进 <think>、正文为空。

生产实测（2026-10-12 11:00，砧板架生图任务）：glm-5.3-flash 把含图片链接的正式答复
整段写进了思考标签，LibreChat 侧 content 只剩 think 块、text 为空，用户收到空白回复。

本补丁在 SSE 流式收尾处（flush 残余 buffer 之后、await agent_task 之前）：
  1. 依赖 _emit._out_all（本补丁在 _emit 各写出点累计的全部输出文本）；
  2. 剥掉 <think> 段与「> 」工具活动行后计算"有效正文"；
  3. 若有效正文为空而思考内容非空 → 取思考内容尾部（默认 900 字符，首行若为
     截断残片则丢弃）补发为一个正文 delta chunk，让用户至少能看到答案。

标记 PATCH-EMPTYTEXT-V1。在服务器上以 root 运行；幂等；改前自动备份。
"""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'PATCH-EMPTYTEXT-V1' in src:
    print('[emptytext v1 already applied]')
    sys.exit(0)

shutil.copy(P, P + '.bak-emptytext-' + stamp)

# ---- A. _emit 状态：累计全部输出文本 ----
anchor_a = '''                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""'''
replacement_a = '''                    if not hasattr(_emit, "_lbuf"):
                        _emit._lbuf = ""
                    if not hasattr(_emit, "_out_all"):
                        _emit._out_all = ""'''
assert anchor_a in src, 'A anchor (_lbuf init) not found'
src = src.replace(anchor_a, replacement_a, 1)

# ---- B. think 工具活动行写出前累计 ----
anchor_b = '''                    if _txt:
                        _chunk = {
                            "id": completion_id, "object": "chat.completion.chunk",
                            "created": created, "model": model,
                            "choices": [{"index": 0, "delta": {"content": _txt}, "finish_reason": None}],
                        }
                        await response.write(f"data: {json.dumps(_chunk)}\\n\\n".encode())'''
replacement_b = '''                    if _txt:
                        _emit._out_all += _txt
                        _chunk = {
                            "id": completion_id, "object": "chat.completion.chunk",
                            "created": created, "model": model,
                            "choices": [{"index": 0, "delta": {"content": _txt}, "finish_reason": None}],
                        }
                        await response.write(f"data: {json.dumps(_chunk)}\\n\\n".encode())'''
assert anchor_b in src, 'B anchor (think activity emit) not found'
src = src.replace(anchor_b, replacement_b, 1)

# ---- C. 正文 delta 写出前累计 ----
anchor_c = '''                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": _item}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\\n\\n".encode())'''
replacement_c = '''                    _emit._out_all += _item
                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": _item}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\\n\\n".encode())'''
assert anchor_c in src, 'C anchor (text delta emit) not found'
src = src.replace(anchor_c, replacement_c, 1)

# ---- D. 收尾 flush 累计 + 空正文保护 ----
anchor_d = '''                _rest = _media_transform(_emit._lbuf)
                _emit._lbuf = ""
                if _rest:
                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": _rest}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\\n\\n".encode())'''
replacement_d = '''                _rest = _media_transform(_emit._lbuf)
                _emit._lbuf = ""
                if _rest:
                    _emit._out_all += _rest
                    content_chunk = {
                        "id": completion_id, "object": "chat.completion.chunk",
                        "created": created, "model": model,
                        "choices": [{"index": 0, "delta": {"content": _rest}, "finish_reason": None}],
                    }
                    await response.write(f"data: {json.dumps(content_chunk)}\\n\\n".encode())

            # PATCH-EMPTYTEXT-V1: 空正文保护——模型偶发把最终答案（含图片链接）整段
            # 写进 <think>，正文为空。从累计输出剥离 think 段与「> 」工具行后若有效
            # 正文为空而思考内容非空，取思考尾部补发为正文，避免用户收到空白回复。
            try:
                _lc_all = getattr(_emit, "_out_all", "") or ""
                if _lc_all:
                    import re as _lc_re
                    _lc_body = _lc_re.sub(r"<think>[\\s\\S]*?</think>", "\\n", _lc_all)
                    _lc_body = _lc_body.replace("<think>", "\\n").replace("</think>", "\\n")
                    _lc_body = "\\n".join(_ln for _ln in _lc_body.splitlines() if not _ln.strip().startswith("> "))
                    _lc_body = _lc_re.sub(r"— 思考了 \\d+ 秒 —", "", _lc_body)
                    _lc_body = _lc_re.sub(r"\\n{3,}", "\\n\\n", _lc_body).strip()
                    if not _lc_body:
                        _lc_think = _lc_re.sub(r"^> [^\\n]*$", "", _lc_all, flags=_lc_re.M)
                        _lc_think = _lc_think.replace("<think>", "\\n").replace("</think>", "\\n")
                        _lc_think = _lc_re.sub(r"— 思考了 \\d+ 秒 —", "", _lc_think)
                        _lc_think = _lc_re.sub(r"\\n{3,}", "\\n\\n", _lc_think).strip()
                        if _lc_think:
                            _lc_rescue = _lc_think[-900:]
                            _lc_cut = _lc_rescue.find("\\n")
                            if _lc_cut > 0:
                                _lc_rescue = _lc_rescue[_lc_cut + 1:]
                            _lc_chunk = {
                                "id": completion_id, "object": "chat.completion.chunk",
                                "created": created, "model": model,
                                "choices": [{"index": 0, "delta": {"content": "\\n\\n" + _lc_rescue}, "finish_reason": None}],
                            }
                            await response.write(f"data: {json.dumps(_lc_chunk)}\\n\\n".encode())
            except Exception:
                pass'''
assert anchor_d in src, 'D anchor (flush + usage comment) not found'
src = src.replace(anchor_d, replacement_d, 1)

open(P, 'w', encoding='utf-8').write(src)
print('[emptytext v1 applied] backup: ' + P + '.bak-emptytext-' + stamp)
