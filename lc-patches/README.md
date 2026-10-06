# LibreChat 界面补丁（单一文件方案）

## 改界面只动一个文件

**`lc_custom.js`** = 全部界面定制的唯一源文件，内含 5 个补丁段（改前先看文件头部的目录注释）：

| 段标记 | 位置 | 功能 |
|---|---|---|
| hide-badges-2026 | `</head>` 前 | 隐藏对 Hermes 无效的工具芯片行 |
| tasks-panel-2026 | `</head>` 前 | ⏰ 定時任務面板 + 定時按钮 |
| think-ui-2026b | `</head>` 前 | 思考块浅色小字、结束后自动收起 |
| skills-picker-v7 | `</head>` 前 | 🧩 技能选择器（按钮在定時鍵右侧）+ 白色 Artifact 卡片 |
| usage-link-2026c | `</body>` 前 | 左栏用量统计图标 |

## 怎么改、怎么生效

```bash
# 1. 编辑 lc_custom.js 对应段落（注意头部警告：段内是 String.raw，勿引入反引号和 ${）
#    ⚠️ 改了段落内容后，把文件里 PATCH_VERSION 的数字 +1，否则部署时不会重新注入！
# 2. 一键部署（scp + 容器内打补丁 + 重启容器，约 40 秒后强刷可见）：
python deploy_lc_patches.py
```

容器里 LibreChat 启动时会缓存 index.html，所以改动必须重启容器才可见——
容器启动命令里带了自动补丁钩子，重启即重打，不用担心。

## 自动化（不怕升级/重建）

服务器 `/opt/lc-run/docker-compose.yml` 里（2026-10-05 配置，备份 `.bak-20261005`）：

- 把 `/opt/lc-patches` 只读挂载进容器；
- api 服务 `command` 覆写为：先 `node /opt/lc-patches/lc_custom.js`，再 `exec npm run backend`。

所以**升级镜像 / `docker compose up -d` 重建容器后，界面定制自动恢复**，无需手动补。

服务器上的手动兜底命令 `lc-repatch`（/usr/local/bin/）= 打补丁 + 修图片目录权限 + 重启。

## 目录结构

- `lc_custom.js` —— 唯一源文件（服务器副本在 `/opt/lc-patches/lc_custom.js`，以本目录为准）
- `deploy_lc_patches.py` —— 一键部署（默认重启；`--no-restart` 只暂存，下次重启生效）
- `archive/` —— 历史：老版本 patch_*.py（v1~v8 时代）、`root-versions/`（曾在仓库根目录的旧 UI 补丁）、
  `migration-tools-20261005/`（本次合并用过的提取/测试工具）、合并时抓的线上快照

## 注意

- 容器内 `/app/client/dist/index.html` 属 root，脚本用「临时文件 + rename」写回（dist 目录对 node 用户可写）。
- 幂等：5 个段标记齐全即跳过；否则先剥哨兵块和全部历史标记块再重注入。
- Hermes 服务端的补丁（`patch_null_*.py`、`patch_activity_v3.py`、`patch_think_v6/v8.py`、`patch_media_v4/v5.py`）
  与本目录无关，仍在仓库根目录，见《部署清单.md》。
