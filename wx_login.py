#!/usr/bin/env python3
"""Weixin iLink QR login runner: calls Hermes qr_login, saves credentials on success."""
import asyncio, sys

sys.path.insert(0, '/home/admin/.hermes/hermes-agent')
HOME = '/home/admin/.hermes'
from gateway.platforms.weixin import qr_login, save_weixin_account  # noqa: E402


def set_env(k, v):
    p = HOME + '/.env'
    try:
        lines = open(p, encoding='utf-8').read().splitlines()
    except FileNotFoundError:
        lines = []
    lines = [l for l in lines if not l.startswith(k + '=')]
    lines.append(k + '=' + v)
    open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


async def main():
    print('waiting for QR...', flush=True)
    creds = await qr_login(HOME)
    if not creds:
        print('LOGIN_FAILED', flush=True)
        return
    aid = creds.get('account_id', '')
    tok = creds.get('token', '')
    base = creds.get('base_url', '')
    uid = creds.get('user_id', '')
    save_weixin_account(HOME, account_id=aid, token=tok, base_url=base, user_id=uid)
    set_env('WEIXIN_ACCOUNT_ID', aid)
    set_env('WEIXIN_TOKEN', tok)
    if base:
        set_env('WEIXIN_BASE_URL', base)
    set_env('WEIXIN_CDN_BASE_URL', 'https://novac2c.cdn.weixin.qq.com/c2c')
    set_env('WEIXIN_DM_POLICY', 'pairing')
    set_env('WEIXIN_ALLOW_ALL_USERS', 'false')
    set_env('WEIXIN_ALLOWED_USERS', '')
    print('LOGIN_OK account_id=' + aid, flush=True)


asyncio.run(main())
