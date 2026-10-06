#!/usr/bin/env python3
"""PATCH-REASONING-2026: api_server accepts TOP-LEVEL reasoning params.

LibreChat custom endpoints forward the per-conversation "Reasoning Effort"
setting as standard OpenAI body params (top-level `reasoning_effort` scalar
or `reasoning` object) on /v1/chat/completions.  Hermes only read them from
`body.model_options` (browser-extension convention), so the setting never
reached the agent.  This patch folds top-level params into model_options so
_run_agent's per-turn reasoning handling applies them.

scp to the server and run with python3, then `hermes gateway restart`.
"""
import re, shutil, sys

TARGET = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
MARK = 'PATCH-REASONING-2026'

OLD = '''    model_options = body.get("model_options")
    if isinstance(model_options, dict):
        overrides["model_options"] = dict(model_options)
    return overrides'''

NEW = '''    model_options = body.get("model_options")
    if isinstance(model_options, dict):
        overrides["model_options"] = dict(model_options)
    # PATCH-REASONING-2026: generic OpenAI clients (LibreChat custom endpoint,
    # /v1/chat/completions) send reasoning as TOP-LEVEL request params, not
    # inside model_options.  Fold them into model_options so the per-turn
    # reasoning handling in _run_agent applies them.
    elif "reasoning_effort" in body or "reasoning" in body:
        folded: Dict[str, Any] = {}
        raw_reasoning = body.get("reasoning")
        if isinstance(raw_reasoning, dict):
            folded["reasoning"] = raw_reasoning
        raw_effort = body.get("reasoning_effort")
        if isinstance(raw_effort, str) and raw_effort.strip():
            folded["reasoning_effort"] = raw_effort.strip()
        elif raw_effort is not None and not isinstance(raw_effort, str):
            folded["reasoning_effort"] = raw_effort
        if folded:
            overrides["model_options"] = folded
    return overrides'''

src = open(TARGET, encoding='utf-8').read()

if MARK in src:
    print('[reasoning patch already present]')
    sys.exit(0)

if OLD not in src:
    sys.exit('target block not found — api_server.py structure changed?')

shutil.copyfile(TARGET, TARGET + '.bak-20261005-reasoning')
src = src.replace(OLD, NEW, 1)
open(TARGET, 'w', encoding='utf-8').write(src)
print('[reasoning patch applied — backup .bak-20261005-reasoning]')
