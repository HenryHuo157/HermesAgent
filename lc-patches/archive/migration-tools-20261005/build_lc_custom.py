#!/usr/bin/env python3
"""Build lc_custom.js: extract the 5 live patch blocks from the container snapshot
and embed them into a single Node patch script (the one file to rule the UI)."""
import re, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SNAP = r'X:\Henry Huo\Hermes Agents\lc-patches\archive\live_index_snapshot_2026-10-05.html'
OUT  = r'X:\Henry Huo\Hermes Agents\lc-patches\lc_custom.js'

# (mark, target, note) in injection order
SECTIONS = [
    ('hide-badges-2026',  'head', '隐藏对 Hermes 无效的工具芯片行（纯 CSS）'),
    ('tasks-panel-2026',  'head', '⏰ 定時任務面板 + 定時按钮'),
    ('think-ui-2026b',    'head', '思考块浅色小字、结束后自动收起（ZCode 风格，取代 thinking-style/working-verbs）'),
    ('skills-picker-v7',  'head', '🧩 技能选择器（按钮在定時鍵右侧）+ 白色 Artifact 卡片（取代 artifact-card/button-v5）'),
    ('usage-link-2026c', 'body', '左栏原生风格用量统计图标（/usage/ 面板入口）'),
]

html = open(SNAP, encoding='utf-8').read()

starts = []
for mark, _, _ in SECTIONS:
    m = re.search(r'<style>\s*/\* PATCH-MARK: ' + re.escape(mark), html)
    assert m, f'mark not found in snapshot: {mark}'
    starts.append((mark, m.start()))
starts.sort(key=lambda x: x[1])

blocks = {}
for i, (mark, start) in enumerate(starts):
    next_start = starts[i + 1][1] if i + 1 < len(starts) else len(html)
    end_style = html.find('</style>', start)
    assert end_style > 0
    end_style += len('</style>')
    end_script = html.find('</script>', start)
    if 0 < end_script and end_script < next_start:
        end = end_script + len('</script>')
    else:
        end = end_style
    assert end <= next_start, f'block {mark} overshoots next block'
    block = html[start:end]
    # safety: template-literal hazards
    assert '`' not in block, f'backtick in {mark}'
    assert '${' not in block, 'template ${} in ' + mark
    blocks[mark] = block
    print(f'{mark:22s} target={SECTIONS[i][2] and dict((m,t) for m,t,_ in SECTIONS)[mark]:4s} len={len(block):5d}  head={block[:60]!r}')

# sanity: every section must appear exactly once in snapshot
for mark, _, _ in SECTIONS:
    assert html.count(blocks[mark]) == 1, f'{mark} count != 1'

LEGACY = [
    # 现行标记也列入清理（重打时先剥掉旧块再注入新块）
    'hide-badges-2026', 'tasks-panel-2026', 'think-ui-2026b', 'usage-link-2026c', 'skills-picker-v7',
    # 历史/被取代版本
    'skills-picker-v1', 'skills-picker-v2', 'skills-picker-v3', 'skills-picker-v4',
    'skills-picker-v5', 'skills-picker-v6',
    'thinking-thin-2026', 'working-verbs-2026', 'greet-welcome-2026b', 'artifact-card-style-2026',
    'usage-link-2026d',
]

removal_fn = r'''
/* ---- 通用清理：按 PATCH-MARK 剥掉历史注入块 ----
   锚定 <style> 内的 MARK 注释，一次性吞掉随后的 style(+)button(+)script 整块。
   块内不会出现 </style>，非贪婪匹配止于本块的第一个 </style>。 */
function stripMark(html, mark){
  const re = new RegExp(
    '<style>\\s*/\\* PATCH-MARK: ' + mark +
    '[\\s\\S]*?</style>' +                       /* CSS 段 */
    '(?:\\s*<button[\\s\\S]*?</button>)?' +       /* usage-link 的按钮 */
    '(?:\\s*<script>[\\s\\S]*?</script>)?\\n?',  /* 可选脚本段 */
    'g');
  return html.replace(re, '');
}
'''

toc = '\n'.join(f' *   [{s[1]:4s}] {s[0]:20s} {s[2]}' for s in SECTIONS)
legacy_js = ',\n  '.join(f"'{m}'" for m in LEGACY)
sections_js = ',\n'.join(
    "  { mark: '%s', target: '%s', html: String.raw`\n%s` }" % (mark, target, blocks[mark])
    for mark, target, _ in SECTIONS
)

HEAD_SENTINEL = 'lc-custom:head:v1'
BODY_SENTINEL = 'lc-custom:body:v1'

js = f"""#!/usr/bin/env node
/* ============================================================================
 * LibreChat 界面定制补丁 —— 唯一源文件（合并自原 5 个 patch_*.py，2026-10-05）
 * ============================================================================
 * 改界面 = 改本文件对应段落，然后二选一生效：
 *   本机:  python deploy_lc_patches.py            （scp 到服务器 + 容器内立即生效）
 *   服务器: docker exec librechat-api node /opt/lc-patches/lc_custom.js
 *
 * 自动化：docker-compose 把 /opt/lc-patches 挂进容器，启动命令先跑本文件再起后端，
 *         所以升级/重建容器后界面定制自动恢复，不再依赖记得手动跑 lc-repatch。
 *
 * 目录（5 段）：
{toc}
 *
 * 注入位置：head 四段插在 </head> 前；usage-link 一段插在 </body> 前（含按钮元素）。
 * 每个目标位置整体包在哨兵注释里，重打时先剥哨兵块再注入，天然幂等。
 * 段落用 String.raw 包裹——反斜杠原样保留（块内 JS 正则不会被转义破坏）；
 * 但仍不要引入反引号 ` 和 ${{ 字符，必要时转义。
 * ==========================================================================*/
'use strict';
const fs = require('fs');

const INDEX = process.env.LC_INDEX_PATH || '/app/client/dist/index.html';
const HEAD_SENTINEL = '{HEAD_SENTINEL}';
const BODY_SENTINEL = '{BODY_SENTINEL}';

/* 历史 PATCH-MARK —— 每次重打前剥掉，兼容老版本注入块（含本文件旧版） */
const LEGACY_MARKS = [
  {legacy_js}
];

const SECTIONS = [
{sections_js}
];
{removal_fn}
function main(){{
  let html;
  try {{
    html = fs.readFileSync(INDEX, 'utf8');
  }} catch (e) {{
    console.error('[lc-custom] cannot read ' + INDEX + ': ' + e.message);
    process.exit(1);
  }}

  /* 0) 快速路径：5 个标记齐全且已规范化 = 已打过，什么都不做 */
  const missing = SECTIONS.filter(s => html.indexOf('PATCH-MARK: ' + s.mark) < 0);
  const normalized = html.indexOf('<!-- ' + HEAD_SENTINEL) >= 0;
  if (missing.length === 0 && normalized) {{
    console.log('[lc-custom] already applied (' + SECTIONS.length + '/' + SECTIONS.length + ' sections)');
    return;
  }}
  if (missing.length === 0) {{
    console.log('[lc-custom] all marks present but legacy format — normalizing into sentinels');
  }}

  /* 1) 剥掉哨兵块（本脚本的旧注入）+ 所有历史标记块 */
  html = html.replace(new RegExp('<!-- ' + HEAD_SENTINEL + ' START -->[\\\\s\\\\S]*?<!-- ' + HEAD_SENTINEL + ' END -->\\\\n?', 'g'), '');
  html = html.replace(new RegExp('<!-- ' + BODY_SENTINEL + ' START -->[\\\\s\\\\S]*?<!-- ' + BODY_SENTINEL + ' END -->\\\\n?', 'g'), '');
  for (const m of LEGACY_MARKS) html = stripMark(html, m);

  /* 2) 按 target 重新注入 */
  const headChunk = '<!-- ' + HEAD_SENTINEL + ' START -->\\n'
    + SECTIONS.filter(s => s.target === 'head').map(s => s.html).join('\\n')
    + '\\n<!-- ' + HEAD_SENTINEL + ' END -->\\n';
  const bodyChunk = '<!-- ' + BODY_SENTINEL + ' START -->\\n'
    + SECTIONS.filter(s => s.target === 'body').map(s => s.html).join('\\n')
    + '\\n<!-- ' + BODY_SENTINEL + ' END -->\\n';

  const hi = html.indexOf('</head>');
  if (hi < 0) throw new Error('</head> not found — LibreChat 结构变了？');
  html = html.slice(0, hi) + headChunk + html.slice(hi);

  const bi = html.indexOf('</body>');
  if (bi < 0) throw new Error('</body> not found');
  html = html.slice(0, bi) + bodyChunk + html.slice(bi);

  /* 3) 写回：index.html 可能是 root 属主，用临时文件 + rename（目录可写即可） */
  const tmp = INDEX + '.lc-custom-tmp';
  fs.writeFileSync(tmp, html);
  fs.renameSync(tmp, INDEX);

  console.log('[lc-custom] injected ' + SECTIONS.length + ' sections (head '
    + SECTIONS.filter(s => s.target === 'head').length + ' + body '
    + SECTIONS.filter(s => s.target === 'body').length + ')');
}}

try {{ main(); }} catch (e) {{
  console.error('[lc-custom] FAILED: ' + e.message);
  process.exit(1);
}}
"""

open(OUT, 'w', encoding='utf-8', newline='\n').write(js)
print(f'\nwrote {OUT} ({os.path.getsize(OUT)} bytes)')
