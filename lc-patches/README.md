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
| version-check-2026 | `</body>` 前 | 📢 版本更新提示（弹窗，用户点更新才刷新） |
| dev-badge-2026 | `</body>` 前 | 🚧 DEV 环境标识（仅 localhost:3081 显示，生产永不显示） |

## 怎么改、怎么生效

```bash
# 1. 编辑 lc_custom.js 对应段落（注意头部警告：段内是 String.raw，勿引入反引号和 ${）
#    ⚠️ 改了段落内容后，把文件里 PATCH_VERSION 的数字 +1，否则部署时不会重新注入！
# 2. 一键部署（scp + 容器内打补丁 + 重启 + 等就绪 + 写版本标记，约 1 分钟）：
python deploy_lc_patches.py            # 推生产
python deploy_lc_patches.py --dev      # 推 Dev（librechat-dev-api，端口 3081）
```

容器里 LibreChat 启动时会缓存 index.html，所以改动必须重启容器才可见——
容器启动命令里带了自动补丁钩子，重启即重打，不用担心。

### 版本更新弹窗（version-check-2026）

`PATCH_VERSION` 同时是**用户所见的版本号**。正常发布（重启路径）会等容器就绪后把版本号写进
容器 `/app/client/dist/picasso-version.txt`（免认证静态文件，Dev/生产通用）；
所有开着的旧页面每 60 秒轮询一次，发现新版本就在右下角弹「🎉 畢卡索有新版本」：

- **立即更新** = `location.reload()`（刷新拿新版）
- **稍後** = 静默 1 小时（localStorage `lc-update-snooze`），期内刷新/重开页面都不再弹

`--no-restart` 只 stage 补丁、**不写版本标记**——旧页面不会收到提示（防止提示了刷新却拿不到新版）；
注意若容器因其他原因重启，staged 版本会自动激活。首次从无标记状态发布后，
所有旧页面（内嵌版本 0）都会收到一次提示，属预期行为。

### 技能选择器的数据双通道（skills-picker-v7）

读法：先 `/skills.json`（**Dev 通道**：`picasso-dev-skills` 从 `/home/dev/.hermes/skills`
生成后 docker cp 进 Dev 容器 dist）→ 失败回退 `/m/skills.json`（**生产通道**：nginx →
`/srv/hermes-share/skills.json`，由 `ai-skills-json` 刷新）。空结果不缓存（防登录后
立即打开撞上应用挂载期）。改了 Dev 技能后跑 `picasso-dev skills` 刷新索引。

## 自动化（不怕升级/重建）

服务器 `/opt/lc-run/docker-compose.yml` 里（2026-10-05 配置，备份 `.bak-20261005`）：

- 把 `/opt/lc-patches` 只读挂载进容器；
- api 服务 `command` 覆写为：先 `node /opt/lc-patches/lc_custom.js`，再 `exec npm run backend`。

所以**升级镜像 / `docker compose up -d` 重建容器后，界面定制自动恢复**，无需手动补。

服务器上的手动兜底命令 `lc-repatch`（/usr/local/bin/）= 打补丁 + 修图片目录权限 + 重启。

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
