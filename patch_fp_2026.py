#!/usr/bin/env python3
"""PATCH-FP-2026: LibreChat 对话 ↔ Hermes 会话严格一一对应。

把 _derive_chat_session_id 的哈希种子从（系统提示+首条用户消息）扩为
（+首条 AI 回复）三元组——让每个 LibreChat 对话严格对应一个独立 Hermes
会话/上下文池，不同对话用相同开场白（如"你好"）不再撞池。
调用点同步改为取首条 assistant 消息（改在 chat_completions 的 else 分支）。

幂等：文件里已有 first_assistant_message 即跳过。
由 hermes-repatch 统一调度；单独跑完需 `hermes gateway restart`。
"""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = open(P, encoding='utf-8').read()
if 'first_assistant_message' in src:
    print('[fp2026 already present]')
    sys.exit(0)

# ---- A. 整体替换 _derive_chat_session_id（按函数边界定位，不依赖上游内部实现）----
start = src.find('def _derive_chat_session_id(')
assert start > 0, 'function _derive_chat_session_id not found'
end = src.find('\n\n\n', start)
assert end > start, 'function end not found'

new_func = '''def _derive_chat_session_id(
    system_prompt: Optional[str],
    first_user_message: str,
    first_assistant_message: str = "",
) -> str:
    """Derive a stable session ID from the conversation's first exchange.

    PATCH-FP-2026: hash the first assistant reply as well, so two different
    conversations that happen to start with the same opening message (e.g.
    "你好") no longer collide into one shared Hermes session/context pool.
    """
    seed = f"{system_prompt or ''}\\n{first_user_message}\\n{first_assistant_message or ''}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"api-{digest}"'''

src = src[:start] + new_func + src[end:]

# ---- B. 调用点：取首条 assistant 消息并传入 ----
anchor_b = '            session_id = _derive_chat_session_id(system_prompt, first_user)'
assert anchor_b in src, 'call site anchor not found — upstream changed?'

replacement_b = '''            first_assistant = ""
            for cm in conversation_messages:
                if cm.get("role") == "assistant":
                    first_assistant = cm.get("content", "") if isinstance(cm.get("content", ""), str) else ""
                    break
            # PATCH-FP-2026: fold the first assistant reply into the fingerprint
            session_id = _derive_chat_session_id(system_prompt, first_user, first_assistant)'''

src = src.replace(anchor_b, replacement_b, 1)

shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src)

data = open(P, 'rb').read()
assert data.count(b'\x00') == 0, 'real NUL bytes present!'
print('[fp2026 applied, file clean]')
