#!/bin/bash
set -e
python3 - <<'PYEOF'
P = '/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py'
s = open(P, encoding='utf-8').read()
anchor = '''                    _lc_body = _lc_re.sub(r"\\n{3,}", "\\n\\n", _lc_body).strip()
                    if not _lc_body:'''
insert = '''                    _lc_body = _lc_re.sub(r"\\n{3,}", "\\n\\n", _lc_body).strip()
                    # 未闭合 think(v8 长任务场景):模型把答案整段写进未关闭的思考块,
                    # LibreChat 解析时全部归入思考、正文为空。补发闭合标签,并把思考
                    # 尾部的实质内容(图片链接/交付说明)补发为正文。
                    _lc_unclosed = _lc_all.count("<think>") > _lc_all.count("</think>")
                    if _lc_unclosed:
                        _lc_close = {
                            "id": completion_id, "object": "chat.completion.chunk",
                            "created": created, "model": model,
                            "choices": [{"index": 0, "delta": {"content": "\\n</think>\\n"}, "finish_reason": None}],
                        }
                        await response.write(f"data: {json.dumps(_lc_close)}\\n\\n".encode())
                        _lc_tail_src = _lc_all.rsplit("<think>", 1)[1]
                        _lc_tail = "\\n".join(_ln for _ln in _lc_tail_src.splitlines() if not _ln.strip().startswith("> "))
                        _lc_tail = _lc_re.sub(r"— 思考了 \\d+ 秒 —", "", _lc_tail)
                        _lc_tail = _lc_re.sub(r"\\n{3,}", "\\n\\n", _lc_tail).strip()
                        if _lc_tail:
                            _lc_rescue = _lc_tail[-1200:]
                            _lc_cut = _lc_rescue.find("\\n")
                            if _lc_cut > 0:
                                _lc_rescue = _lc_rescue[_lc_cut + 1:]
                            _lc_chunk = {
                                "id": completion_id, "object": "chat.completion.chunk",
                                "created": created, "model": model,
                                "choices": [{"index": 0, "delta": {"content": _lc_rescue}, "finish_reason": None}],
                            }
                            await response.write(f"data: {json.dumps(_lc_chunk)}\\n\\n".encode())
                    if not _lc_body:'''
assert s.count(anchor) == 1, 'occurrences=%d' % s.count(anchor)
s = s.replace(anchor, insert, 1)
open(P, 'w', encoding='utf-8').write(s)
print('unclosed-think branch inserted')
PYEOF
python3 -c "import ast; ast.parse(open('/home/dev/.hermes/hermes-agent/gateway/platforms/api_server.py', encoding='utf-8').read()); print('AST OK')"
sudo -u dev -H /home/dev/.local/bin/hermes gateway restart 2>&1 | tail -1
sleep 3
ss -tlnp | grep 8643 | head -1
