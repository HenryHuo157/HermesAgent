#!/usr/bin/env python3
"""green_check v2：把活动时间线完成符号从灰色 ✓ 换成绿色 ✅。

v2 改为内容定位（原版按行号 lines[4283]，升级后必失效）。
仅当 api_server 处于 v6 状态（PATCH-THINK-V6 存在）且未到 v8 时执行；
v3 之前没有该行、v8 之后符号带 \\n\\n 后缀，两种情况都自动跳过。
"""
import shutil, sys, datetime

P = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

CHECK = chr(0x2713)   # 灰色对勾 ✓
GREEN = chr(0x2705)   # 绿色对勾 ✅

src = open(P, encoding='utf-8').read()

if '_v8short' in src:
    print('[green_check skipped: chain already at v8]')
    sys.exit(0)
if 'PATCH-THINK-V6' not in src:
    print('[green_check skipped: v6 not applied yet]')
    sys.exit(0)

old = '_txt = " ' + CHECK + chr(92) + 'n"'
new = '_txt = " ' + GREEN + chr(92) + 'n"'
if old not in src:
    print('[green_check skipped: checkmark line not found (already green?)]')
    sys.exit(0)

shutil.copy(P, P + '.bak.' + stamp)
open(P, 'w', encoding='utf-8').write(src.replace(old, new, 1))
print('[green_check applied]')
