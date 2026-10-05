# -*- coding: utf-8 -*-
# 2026-10-05 產品更名 Luma → 畢卡索（Picasso）：服務器端精準替換（先備份）
# 注意：LumaShare 是 NAS 實際共享名（CIFS 掛載路徑），本次不改
import io, json, shutil, sys

STAMP = "20261005"
PICASSO_ESC = "\\u7562\\u5361\\u7d22"  # 畢卡索，與 jobs.json 的 ensure_ascii 風格一致

def patch(path, pairs, expect=1):
    with io.open(path, "r", encoding="utf-8") as f:
        s = f.read()
    orig = s
    n_total = 0
    for old, new in pairs:
        n_total += s.count(old)
        s = s.replace(old, new)
    if s == orig:
        print("NOCHANGE", path)
        return False
    shutil.copy2(path, path + ".bak-" + STAMP)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(s)
    print("PATCHED", path, "replacements:", n_total)
    return True

# 1) SOUL.md —— 自我認知；只動身份句，不碰 LumaShare（NAS 共享名）
patch("/home/admin/.hermes/SOUL.md", [
    ("Your name is Luma", "Your name is Picasso (畢卡索)"),
    ("you are Luma, Mainplan", "you are 畢卡索（英文名 Picasso）, Mainplan"),
    ("— Luma ✨", "— 畢卡索 ✨"),
])

# 2) cron/jobs.json —— 早報任務名/提示詞/標題/署名（文件是 ensure_ascii 轉義風格）
ok = patch("/home/admin/.hermes/cron/jobs.json", [
    ("Luma", PICASSO_ESC),
])
if ok:
    json.load(io.open("/home/admin/.hermes/cron/jobs.json", "r", encoding="utf-8"))
    print("jobs.json JSON validate: OK")

# 3) 用量面板標題（3 處）
patch("/opt/usagepanel/app.py", [
    ("Luma 用量统计", "畢卡索 用量统计"),
])

# 4) LibreChat 標題（.env 的 APP_TITLE）
patch("/opt/lc-run/.env", [
    ("APP_TITLE=Luma", "APP_TITLE=畢卡索"),
])

print("ALL DONE")
