# LibreChat 界面补丁（单一文件方案）

## 改界面只动一个文件

**`lc_custom.js`** = 全部界面定制的唯一源文件，内含 8 个补丁段（改前先看文件头部的目录注释）：

| 段标记 | 位置 | 功能 |
|---|---|---|
| hide-badges-2026 | `</head>` 前 | 隐藏对 Hermes 无效的工具芯片行 |
| tasks-panel-2026 | `</head>` 前 | ⏰ 定時任務面板 + 定時按钮 |
| think-ui-2026b | `</head>` 前 | 思考块浅色小字、结束后自动收起 |
| skills-picker-v7 | `</head>` 前 | 🧩 技能选择器（按钮在定時鍵右侧）+ 白色 Artifact 卡片 |
| effort-selector-2026 | `</head>` 前 | 🧠 思考程度选择器（默认/关/低/中/高循环） |
| usage-link-2026c | `</body>` 前 | 左栏用量统计图标 |
| version-check-2026 | `</body>` 前 | 📢 版本更新提示（弹窗，用户点更新才刷新）+ 常驻版本徽章 |
| dev-badge-2026 | `</body>` 前 | 🚧 DEV 环境标识（仅 localhost:3082 显示，生产永不显示） |
| desktop-pet-2026 | `</body>` 前 | 🐾 桌面小宠物「小畢」（漫游/摸摸/睡觉/右键回家） |

## 怎么改、怎么生效（零重启）

```bash
# 1. 编辑 lc_custom.js 对应段落（注意头部警告：段内是 String.raw，勿引入反引号和 ${）
#    ⚠️ 改了段落内容后，把文件里 PATCH_VERSION 的数字 +1（= 用户在徽章/弹窗里看到的版本号）
# 2. 一键发布（scp + nginx 分发自检 + 写版本标记，约 5 秒，容器零重启、用户零打断）：
python deploy_lc_patches.py            # 推生产
python deploy_lc_patches.py --dev      # 推 Dev（nginx 3082 分发，浏览器 localhost:3082 刷新即见）
```

老页面由版本弹窗提示、用户点「立即更新」/点左下角徽章刷新后才进入新版——发布过程和结果都不打断任何人。

### 双模式架构（2026-10-07 零重启改造）

lc_custom.js 是**双模式单文件**：

- **浏览器模式**：nginx 对页面 `sub_filter` 注入 `<script src="/lc_custom.js"></script>`（`Cache-Control: no-cache`），浏览器直接加载本文件——检测到 `window` 就把 9 段补丁挂到页面（style/元素走 innerHTML，script 重建执行）。
- **注入器模式（node，应急）**：检测到 Node 环境时可用。默认 no-op（容器启动钩子安全空转）；`--strip` 剥离 index.html 内联块（迁移用）；`--inject-legacy` 恢复旧式内联注入（nginx 分发不可用时的应急回退）。

容器里 LibreChat 缓存 index.html 的老问题从此无关——界面发布不再触碰容器。`--restart` 参数保留给应急；`--strip-restart` 是一次性迁移工具（已于 2026-10-07 对生产执行完毕）。

### 版本更新弹窗 + 常驻版本徽章（version-check-2026）

`PATCH_VERSION` 同时是**用户所见的版本号**。发布把版本号写进
容器 `/app/client/dist/picasso-version.txt`（免认证静态文件，Dev/生产通用）；
所有开着的旧页面每 60 秒轮询一次，发现新版本就在右下角弹「🎉 畢卡索有新版本」：

- **立即更新** = `location.reload()`（刷新拿新版）
- **稍後** = 静默 1 小时（localStorage `lc-update-snooze`），期内刷新/重开页面都不再弹

**左下角常驻版本徽章**：平时低调显示当前版本号（如 `v11`），有更新时变橙色显示
`v11 ↑ v12`；**点击徽章随时手动检查并唤出更新卡片（无视「稍後」静默）**——
弹窗被关掉后想更新，点它就行。无更新时点击显示「✓ 已是最新」。

`--no-restart` 只 stage 补丁、**不写版本标记**——旧页面不会收到提示（防止提示了刷新却拿不到新版）；
注意若容器因其他原因重启，staged 版本会自动激活。首次从无标记状态发布后，
所有旧页面（内嵌版本 0）都会收到一次提示，属预期行为。

### 技能选择器的数据双通道（skills-picker-v7）

读法：先 `/skills.json`（**Dev 通道**：`picasso-dev-skills` 从 `/home/dev/.hermes/skills`
生成后 docker cp 进 Dev 容器 dist）→ 失败回退 `/m/skills.json`（**生产通道**：nginx →
`/srv/hermes-share/skills.json`，由 `ai-skills-json` 刷新）。空结果不缓存（防登录后
立即打开撞上应用挂载期）。改了 Dev 技能后跑 `picasso-dev skills` 刷新索引。

## 自动化（不怕升级/重建）

- nginx（/etc/nginx/conf.d/hermes-public.conf，备份 `.bak-20261007-zero-restart`）：生产 443 的 `location /` 带 sub_filter + `location = /lc_custom.js`（root /opt/lc-patches）；Dev 走独立 server 块 `listen 127.0.0.1:3082`（root /opt/lc-patches-dev → 容器 3081）。
- **升级镜像 / 重建容器后界面自动恢复，且连"重打补丁"都不需要**：新容器从镜像拿到干净的 index.html，nginx sub_filter 照常注入脚本标签，界面照常工作。
- 容器启动钩子（compose command 里的 `node /opt/lc-patches/lc_custom.js || true`）保留但 no-op，compose 无需改动。
- 服务器上的 `lc-repatch`（/usr/local/bin/）已无日常用途（保留做图片目录权限修复）。

## 目录结构

- `lc_custom.js` —— 唯一源文件（服务器副本在 `/opt/lc-patches/lc_custom.js`，Dev 副本在 `/opt/lc-patches-dev/`，以本目录为准）
- `deploy_lc_patches.py` —— 一键部署（默认重启+写版本标记；`--dev` 推 Dev；`--no-restart` 只暂存不写标记）
- `archive/` —— 历史：老版本 patch_*.py（v1~v8 时代）、`root-versions/`（曾在仓库根目录的旧 UI 补丁）、
  `migration-tools-20261005/`（本次合并用过的提取/测试工具）、合并时抓的线上快照

## 注意

- 容器内 `/app/client/dist/index.html` 属 root，脚本用「临时文件 + rename」写回（dist 目录对 node 用户可写）。
- 幂等：全部段标记齐全 + 版本号一致即跳过；否则先剥哨兵块和全部历史标记块再重注入。
- Hermes 服务端的补丁（`patch_null_*.py`、`patch_activity_v3.py`、`patch_think_v6/v8.py`、`patch_media_v4/v5.py`）
  与本目录无关，仍在仓库根目录，见《部署清单.md》。
