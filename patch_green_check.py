#!/usr/bin/env python3
"""Swap the gray checkmark for the green emoji in the activity mirror."""
path = '/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py'
lines = open(path, encoding='utf-8').read().splitlines()
assert chr(0x2713) in lines[4283], 'line 4284 has no checkmark: ' + repr(lines[4283])
lines[4283] = '                        _txt = " ' + chr(0x2705) + chr(92) + 'n"'
open(path, 'w', encoding='utf-8').write(chr(10).join(lines) + '\n')
print('replaced:', lines[4283])
