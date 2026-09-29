# Luma · 敏寶團隊 AI（Hermes Agent 部署工程）

Mainplan（敏寶）的團隊 AI 助手 **Luma** 的完整部署工程：基於 Hermes Agent（雲端沙盒 Agent）+ LibreChat（網頁前端）+ 飛書/微信渠道，AI 大腦為 GLM-5.3-Flash（Z.ai 編程套餐端點）。

## 架構一覽

```
飛書/微信 ──→ Hermes Gateway（消息渠道，配對制）
網頁 https://<server> ──→ LibreChat（多用户賬號）──→ Hermes API Server(8642)
                                        └→ 網盤 filebrowser / 文件同步 Syncthing / 定時任務面板
 Hermes Agent ──→ 雲端沙盒（bash/聯網搜索/圖像生成/LibreOffice 文檔工具鏈）
```

## 目錄說明

| 路徑 | 內容 |
|---|---|
| `部署清单.md` | **主文檔**：全部服務、入口、賬號位置、補丁清單、運維命令（敏感值已脱敏，完整值見本地 password.txt） |
| `同事使用说明.md` | 給全員的使用指南（繁體） |
| `lc-patches/` | LibreChat 界面補丁庫（技能選擇器、思考樣式、工作動詞、定時面板等；服務器上一鍵 `lc-repatch` 重打） |
| `patch_*.py`（根目錄） | Hermes 側源碼補丁歷史（NUL 字節修復、活動時間線、MEDIA 内嵌、思考塊等） |
| `taskspanel_app.py` | 定時任務面板後端（每用户自助創建 cron，systemd 服務） |
| `feishu_setup.py` / `wx_login.py` | 飛書/微信渠道接入脚本 |
| `dump_skills_json.py` | 技能索引導出（供前端技能選擇器） |
| `chatpage/` | 早期自製聊天頁（已弃用，備份） |
| `LibreChat部署包/` | 給同事自行部署的獨立安装包（無密鑰） |
| `setup_hermes_access.sh` 等 | 早期部署脚本（歷史存檔） |

## 服務器關鍵路徑（ ssh root@<server-ip> ）

- Hermes：`/home/admin/.hermes/`（config.yaml / SOUL.md / skills/）
- LibreChat：`/opt/lc-run/`（compose）、`/opt/librechat/librechat.yaml`
- 界面補丁庫：`/opt/lc-patches/`（重打命令 `lc-repatch`）
- 每日備份：`/opt/backups/`（7 天滾動）

## 安全約定

- 所有真實密鑰/密碼只存服務器與本地 `password.txt`（已 gitignore），倉庫内一律脱敏
- 雲端沙盒全放行（approvals: off），本地文件通過專用共享目錄 + 只讀優先原則交換
