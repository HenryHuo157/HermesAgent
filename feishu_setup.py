#!/usr/bin/env python3
"""Feishu device-code onboarding runner: QR scan -> app credentials -> env."""
import sys

sys.path.insert(0, '/home/admin/.hermes/hermes-agent/plugins/platforms/feishu')
HOME = '/home/admin/.hermes'
from adapter import _begin_registration, _poll_registration  # noqa: E402


def set_env(k, v):
    p = HOME + '/.env'
    try:
        lines = open(p, encoding='utf-8').read().splitlines()
    except FileNotFoundError:
        lines = []
    lines = [l for l in lines if not l.startswith(k + '=')]
    lines.append(k + '=' + v)
    open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def main():
    print('starting device flow...', flush=True)
    reg = _begin_registration('feishu')
    print('QR_URL=' + reg['qr_url'], flush=True)
    print('EXPIRE_IN=%s USER_CODE=%s' % (reg['expire_in'], reg['user_code']), flush=True)

    res = _poll_registration(
        device_code=reg['device_code'],
        interval=reg['interval'],
        expire_in=reg['expire_in'],
        domain='feishu',
    )
    if not res:
        print('LOGIN_FAILED', flush=True)
        return

    app_id = res.get('app_id', '')
    app_secret = res.get('app_secret', '')
    set_env('FEISHU_APP_ID', app_id)
    set_env('FEISHU_APP_SECRET', app_secret)
    set_env('FEISHU_DOMAIN', res.get('domain', 'feishu'))
    set_env('FEISHU_CONNECTION_MODE', 'websocket')
    print('LOGIN_OK app_id=' + app_id, flush=True)


main()
