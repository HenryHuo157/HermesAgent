#!/usr/bin/env python3
"""Compare live container index.html blocks vs local patch scripts' BLOCK payloads."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SNAP = r'X:\Henry Huo\Hermes Agents\lc-patches\archive\live_index_snapshot_2026-10-05.html'
SCRIPTS = {
    'hide-badges-2026':  r'X:\Henry Huo\Hermes Agents\lc-patches\patch_hide_badges.py',
    'tasks-panel-2026':  r'X:\Henry Huo\Hermes Agents\lc-patches\patch_tasks_panel.py',
    'think-ui-2026b':    r'X:\Henry Huo\Hermes Agents\lc-patches\patch_think_ui_v2.py',
    'usage-link-2026c':  r'X:\Henry Huo\Hermes Agents\lc-patches\patch_usage_link.py',
    'skills-picker-v7':  r'X:\Henry Huo\Hermes Agents\lc-patches\patch_skills_picker_v7.py',
    # dead candidates
    'working-verbs':     r'X:\Henry Huo\Hermes Agents\lc-patches\patch_working_verbs.py',
    'greet-welcome':     r'X:\Henry Huo\Hermes Agents\lc-patches\patch_greet_welcome.py',
    'artifact-card':     r'X:\Henry Huo\Hermes Agents\lc-patches\patch_artifact_card.py',
    'button-v5':         r'X:\Henry Huo\Hermes Agents\lc-patches\patch_button_v5.py',
    'thinking-style':    r'X:\Henry Huo\Hermes Agents\lc-patches\patch_thinking_style.py',
}

html = open(SNAP, encoding='utf-8').read()

print('=== live blocks (from <style> w/ PATCH-MARK to </script>) ===')
live = {}
for m in re.finditer(r'<style>\s*/\* PATCH-MARK: ([a-zA-Z0-9-]+)', html):
    mark = m.group(1)
    end = html.find('</script>', m.start())
    block = html[m.start():end + len('</script>')]
    live.setdefault(mark, []).append(block)
    print(f'{mark:22s} start={m.start():6d} len={len(block):6d}')

print()
print('=== script BLOCK vs live ===')
for mark, path in SCRIPTS.items():
    src = open(path, encoding='utf-8').read()
    bm = re.search(r'BLOCK = r"""(.*?)"""', src, re.S)
    if not bm:
        print(f'{mark:22s} NO BLOCK in script')
        continue
    block = bm.group(1)
    if block.startswith('<style>'):
        inner = block[len('<style>'):]
    else:
        inner = block
    cnt = html.count(block)
    cnt_inner = html.count(inner)
    copies = len(live.get(mark, []))
    print(f'{mark:22s} script_block_len={len(block):6d} verbatim_in_live={cnt} inner_in_live={cnt_inner} live_copies={copies}')
    if cnt == 0 and cnt_inner == 0 and copies:
        # show first diff line vs live copy
        lb = live[mark][0]
        if block.startswith('<style>') and not lb.startswith('<style>'):
            lb2 = '<style>' + lb
        else:
            lb2 = lb
        for i, (a, b) in enumerate(zip(lb2, block)):
            if a != b:
                print(f'    first diff at {i}: live=...{lb2[max(0,i-40):i+40]!r} script=...{block[max(0,i-40):i+40]!r}')
                break
        else:
            print(f'    prefix equal, len live={len(lb2)} script={block}')

print()
print('=== script MARK constants ===')
for mark, path in SCRIPTS.items():
    src = open(path, encoding='utf-8').read()
    mm = re.search(r"^MARK = '([^']+)'", src, re.M)
    old = re.search(r"OLD_MARK = '([^']+)'", src, re.M)
    print(f'{mark:22s} script at {path.split(chr(92))[-1]:32s} MARK={mm.group(1) if mm else "?"}' + (f' OLD={old.group(1)}' if old else ''))
