#!/bin/bash
python3 - <<'EOF'
import re
s = open('/tmp/hooks.js', encoding='utf-8', errors='replace').read()
print('== THINK enum-ish ==')
for m in list(re.finditer(r'THINK', s))[:6]:
    i = m.start()
    print(repr(s[max(0,i-140):i+140])); print('======')
print('== <think literal ==')
for m in list(re.finditer(r'<think', s))[:6]:
    i = m.start()
    print(repr(s[max(0,i-160):i+160])); print('======')
print('== think part creation ==')
for m in list(re.finditer(r'type[:=][^,;]{0,20}think', s))[:8]:
    i = m.start()
    print(repr(s[max(0,i-120):i+160])); print('======')
EOF
