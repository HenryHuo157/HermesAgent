# AGENTS.md — 本仓库工作约定（AI 助手每次会话自动读取）

## 这个仓库是什么

「畢卡索 (Picasso)」团队 AI 的部署工程仓库。**生产环境（Live）有真实同事在用**：
https://47.243.79.144（LibreChat 主界面）+ Hermes Agent + 飞书/微信渠道。
服务器：`ssh root@47.243.79.144`（已配密钥免密）。全部服务/入口/账号位置/运维命令见《部署清单.md》。

## 铁律：改动走 Dev，发布挑时机

1. **任何改动先在 Dev 环境验证，再上生产**。Dev 对用户完全不可见（无 nginx 条目、端口只绑本机回环、防火墙未放行）。
2. Dev = 服务器上的按需环境（Dev Hermes 8643 + Dev LibreChat 3081 + 独立补丁库/数据库/账号体系）：
   - 启停（root）：`picasso-dev start`（约 1.1G 内存）／`picasso-dev stop`（**用完必须停**）
   - 本机访问：`ssh -L 3081:127.0.0.1:3081 root@47.243.79.144` 后开 http://localhost:3081
   - 详情见《部署清单.md》「Live/Dev 双环境」章节
3. **UI 补丁**：改 `lc-patches/lc_custom.js` → 把 `PATCH_VERSION` +1 → `python lc-patches/deploy_lc_patches.py --dev` 在 Dev 验证 → 去掉 `--dev` 上生产。发布脚本自动等容器就绪后写版本标记，旧页面 60 秒内弹「有新版本」，用户点「立即更新」才刷新。
   **改 UI 补丁前 AI 必须自动确保 Dev 在跑**：`ssh root@47.243.79.144 "picasso-dev start"`（deploy --dev 要往容器里打补丁，容器没跑会失败）；部署完提醒用户刷新 http://localhost:3081 查看效果。用户侧等价操作 = 双击仓库根目录 `Dev版-打开.bat`（幂等，已在跑会直接跳到开隧道+浏览器）。
4. **Hermes 源码补丁**：补丁先 scp 到服务器 `/opt/hermes-patches/` → `hermes-repatch-dev --sync`（派生到 dev 补丁库并重打）→ Dev 验证 → 生产再跑 `hermes-repatch`。注意：升级生产 Hermes 后重建 Dev 必须重跑 `server-tools/fix-dev-paths.sh`（editable pip 安装的路径改写）。
5. **生产重启（LibreChat 容器 / Hermes 网关）会打断正在使用的用户**——发布时机必须由用户（Henry）决定，默认低峰执行；需要预放时用 `--no-restart` stage。
6. 上了生产后在本地仓库打 tag：`git tag -a live-YYYYMMDD -m "..." && git push --tags`。
7. 敏感信息（password.txt、*.env、密钥/密码类文件）已 gitignore：绝不入库、绝不上传外部服务。

## 本机环境注意事项（Windows）

- Shell 是 Windows cmd：没有 ls/head/tail/grep 等命令；**含 `$(...)`、嵌套引号、管道的远端命令经 cmd 传递会损坏——一律写成脚本文件 `scp` 到服务器 `/tmp/` 执行**（先 `sed -i 's/\r$//'` 去 CRLF）。
- git 不在默认 PATH：用完整路径 `"C:\Program Files\Git\bin\git.exe"` 或先 `set "PATH=C:\Program Files\Git\bin;%PATH%"`。
- 本机无 Docker/WSL；Dev 环境在服务器上（见上），本机只做仓库编辑和部署脚本触发。
- 本机浏览器可经 ZCode 内置浏览器（browser-use）做 Dev 页面实测，SSH 隧道用后台任务开着。
- 网页浏览/抓取优先用 Decodo MCP（全局约定，见 `~/.zcode/AGENTS.md`）。

## 文档地图

- 《部署清单.md》—— 主文档：全部服务、入口、补丁清单、运维命令、Live/Dev 双环境详情
- `lc-patches/README.md` —— 界面补丁结构与版本弹窗机制
- `server-tools/` —— 服务器侧脚本源码（每日备份、监控告警、Dev 环境构建/控制/验证）
