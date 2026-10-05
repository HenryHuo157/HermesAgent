#!/usr/bin/env python3
"""ZCode 风格思考块补丁 v2（替代 patch_thinking_style.py + patch_working_verbs.py）。

功能：
1. 思考块整体浅色小字（#9ca3af / 12.5px），链接、代码同步调浅，去掉卡片底色；
2. 回答结束后自动把展开的思考块收起（流式过程中保持展开，可随时手动展开）；
3. 读取 Hermes v7 写入的 "— 思考了 N 秒 —" 标记：隐藏标记行，把标题改成
   「思考 · 持續了 N 秒」（ZCode 同款）。

对旧消息（无时长标记）只做 1，不强制收起。
"""
import re, subprocess, sys

INDEX = '/app/client/dist/index.html'
MARK = 'think-ui-2026b'

BLOCK = r"""<style>
/* PATCH-MARK: think-ui-2026b — ZCode 风格思考块：浅色小字、紧凑 */
.group\/reasoning, .group\/reasoning-compact{
  font-size:12.5px !important;
  color:#9ca3af !important;
}
.group\/reasoning :is(p,span,div,li,ul,ol,blockquote,em,strong,b,i,h1,h2,h3,h4,h5,h6,td,th),
.group\/reasoning-compact :is(p,span,div,li,ul,ol,blockquote,em,strong,b,i){
  color:#9ca3af !important;
}
.group\/reasoning p, .group\/reasoning-compact p{
  margin:0 0 1px !important;
  line-height:1.6 !important;
}
.group\/reasoning a, .group\/reasoning-compact a{
  color:#8aa2c4 !important;
  text-decoration-color:rgba(138,162,196,.45) !important;
}
.group\/reasoning :is(code,pre), .group\/reasoning-compact :is(code,pre){
  font-size:11px !important;
  color:#9ca3af !important;
  background:rgba(130,140,160,.08) !important;
}
.group\/reasoning .rounded-lg, .group\/reasoning .rounded-2xl,
.group\/reasoning-compact .rounded-2xl{
  background:transparent !important;
  border-color:rgba(130,140,160,.16) !important;
}
.group\/reasoning blockquote, .group\/reasoning-compact blockquote{
  border-color:rgba(130,140,160,.25) !important;
}
.group\/reasoning button span{ color:#98a1b0 !important; }
.group\/reasoning-compact .tool-status-text{ color:#98a1b0 !important; font-weight:500 !important; }
</style>
<script>
/* PATCH-MARK: think-ui-2026b — 完成后收起 + 标题「思考 · 持續了 N 秒」 */
(function(){
  var MARK_RE = /思考了\s*(\d+)\s*秒/;
  function upgrade(block, anyStreaming){
    var leaves = block.querySelectorAll('p,div,span');
    var el = null, m = null;
    for (var j = 0; j < leaves.length; j++){
      if (leaves[j].querySelector('p,div,span')) continue;
      var mm = (leaves[j].textContent || '').match(MARK_RE);
      if (mm){ el = leaves[j]; m = mm; break; }
    }
    if (!el) return;
    if (el.style.display !== 'none') el.style.display = 'none';
    var label = block.querySelector('button[aria-expanded] span.truncate')
             || block.querySelector('.tool-status-text');
    if (label) label.textContent = '思考 · 持續了 ' + m[1] + ' 秒';
    // 已结束的消息才自动收起（生成中的保持展开，可实时看活动行）
    if (anyStreaming) return;
    if (!block.dataset.tuiCollapsed && !block.dataset.tuiUserToggled){
      var btn = block.querySelector('button[aria-expanded="true"]');
      if (btn){ block.dataset.tuiCollapsed = '1'; btn.click(); }
    }
  }
  function enhance(){
    var anyStreaming = !!document.querySelector('.submitting');
    var blocks = document.querySelectorAll('.group\\/reasoning, .group\\/reasoning-compact');
    for (var i = 0; i < blocks.length; i++) upgrade(blocks[i], anyStreaming);
  }
  document.addEventListener('click', function(e){
    var btn = e.target && e.target.closest && e.target.closest('.group\\/reasoning button, .group\\/reasoning-compact button');
    if (btn){
      var block = btn.closest('.group\\/reasoning, .group\\/reasoning-compact');
      if (block) block.dataset.tuiUserToggled = '1';
    }
  }, true);
  var t = null;
  var mo = new MutationObserver(function(){
    if (t) clearTimeout(t);
    t = setTimeout(enhance, 900);
  });
  function start(){
    if (document.body){ mo.observe(document.body, {childList:true, subtree:true}); enhance(); }
    else setTimeout(start, 300);
  }
  start();
})();
</script>"""

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

r = run(f'docker exec librechat-api cat {INDEX}')
if r.returncode != 0:
    sys.exit('cannot read index.html: ' + r.stderr)
html = r.stdout

# 移除被本补丁替代的旧块（thinking_style 的 CSS、working_verbs 的 CSS+JS），
# 以及本补丁的旧版本（便于升级重注入）
for pat in (
    r'<style>(?:(?!</style>).)*?thinking-thin-2026(?:(?!</style>).)*?</style>\n?',
    r'<style>(?:(?!</style>).)*?working-verbs-2026(?:(?!</style>).)*?</style>\n?',
    r'<script>(?:(?!</script>).)*?working-verbs-2026(?:(?!</script>).)*?</script>\n?',
    r'<style>(?:(?!</style>).)*?think-ui-2026b(?:(?!</style>).)*?</style>\n?',
    r'<script>(?:(?!</script>).)*?think-ui-2026b(?:(?!</script>).)*?</script>\n?',
):
    html = re.sub(pat, '', html, flags=re.S)

if MARK in html:
    print('[think-ui v2 already present]')
    sys.exit(0)

assert '</head>' in html, 'no </head>'
html = html.replace('</head>', BLOCK + '\n</head>', 1)
open('/tmp/lc_index_thinkui2.html', 'w', encoding='utf-8').write(html)
r2 = run('docker cp /tmp/lc_index_thinkui2.html librechat-api:' + INDEX)
if r2.returncode != 0:
    sys.exit('docker cp failed: ' + r2.stderr)
print('[think-ui v2 injected]')
