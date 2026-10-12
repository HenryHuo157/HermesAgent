---
name: picasso-deploy
description: 畢卡索（Picasso AI，仓库 X:\Henry Huo\Hermes Agents）的 Dev→Live 开发发布模式。凡是改 LibreChat 界面补丁、Hermes 补丁、独立面板服务（pwpanel/usagepanel 类）、librechat.yaml、批量建号/改库，或任何"上线/发布到 Live/生产"相关的工作，都用本 Skill 的流程：先 Dev 验证、汇报、等用户明示才推生产。也适用于排查"生产有真实同事在用"的相关问题。
---

# Picasso Dev→Live 开发发布模式

生产环境（https://47.243.79.144，LibreChat 主界面 + Hermes 网关）**有真实同事在用**。
一切改动的唯一合法路径：**Dev 改 → Dev 验证 → 停下来汇报 → 用户明示"上 Live" → 推生产 → 生产验证 → commit + tag**。
仓库根目录 AGENTS.md 与《部署清单.md》是权威文档，与本 Skill 冲突时以更严格者为准。

## 0. 环境

| | Dev | Live/生产 |
|---|---|---|
| LibreChat 容器 | librechat-dev-api（127.0.0.1:3081） | librechat-api（127.0.0.1:3080） |
| Mongo 容器/库 | librechat-dev-mongo / LibreChatDev | librechat-mongo / LibreChat |
| 入口 | ssh 隧道 `-L 3082:127.0.0.1:3082` → http://localhost:3082（nginx 3082 分发，与生产同构） | https://47.243.79.144 |
| Hermes | 8643（/home/dev/.hermes/） | 8642（admin 用户） |
| 补丁库 | /opt/lc-patches-dev/ + /opt/hermes-patches 派生 | /opt/lc-patches/ |
| 开关 | `picasso-dev start` / `picasso-dev stop`（用完必须停；已在跑会跳过） | 常驻 |

服务器：`ssh root@47.243.79.144`（已配密钥免密）。本机无 Docker，所有容器操作走 ssh。

## 1. 发布通道决策树

改什么 → 走哪条通道：

1. **界面/前端行为**（横幅、菜单、按钮、默认模型…）→ `lc-patches/lc_custom.js` 界面补丁（零重启）
2. **独立小服务**（改密码、面板类）→ 仿 `server-tools/pwpanel/`：Python stdlib http.server 绑 127.0.0.1 + nginx location 分发 + systemd；需要密码学操作时 `docker exec` 进 LibreChat 容器用它的 bcryptjs/mongodb 驱动
3. **Hermes 源码/配置** → 补丁 scp 到 /opt/hermes-patches/ → `hermes-repatch-dev --sync` → Dev 验证 → 生产 `hermes-repatch`（网关重启，低峰+确认）
4. **librechat.yaml / 容器升级** → 低峰+用户确认（会打断用户）
5. **数据库变更**（建号、改字段）→ 仿 `server-tools/bulk_create_users.py`：脚本化、幂等、支持 --dev/--prod、dry-run 默认
6. **nginx 配置** → 改前备份 + `nginx -t` 失败自动还原的幂等脚本（仿 `server-tools/pwpanel/add-*-pw-location.py`），reload 毫秒级但仍是生产改动，先问

## 2. 标准流程（每一条通道都一样）

1. **本地改代码**（仓库 server-tools/ 或 lc-patches/，可复用为先）
2. **Dev 部署**：`python lc-patches/deploy_lc_patches.py --dev`（补丁自动 PATCH_VERSION+1！改任何段内容必须 +1，否则用户页面不刷新）或 scp 脚本
3. **Dev 验证**（缺一不可）：
   - API 层：ssh 到服务器 curl 全链路（登录、改密、删除等，含**错误场景**：错密码、越权、边界值）
   - 数据层：mongosh 查库确认实际效果（`docker exec librechat-dev-mongo mongosh --quiet LibreChatDev --eval ...`）
   - 浏览器层：ZCode 内置浏览器经 localhost:3082 实测 UI（生产是自签证书，内置浏览器过不去，生产 UI 验证靠同代码同构推断 + 让用户刷新确认）
4. **汇报 + 等指示**：告诉用户验证结果，**明确停下问"要不要上生产"**。用户没说"上/推 Live"，绝不碰生产——零重启发布也不例外
5. **推生产**：同一份代码 `--prod` / 正式 deploy；生产验证重复第 3 步的 API+数据层（UI 能测则测）
6. **收尾**：更新《部署清单.md》→ `git commit` → `git tag -a live-YYYYMMDD` → `git push origin main --tags`。敏感文件（*password*、CSV 密码清单）已被 gitignore/Syncthing 排除，**绝不提交**

## 3. 硬踩坑记录（每条都真踩过，勿再踩）

**本机（Windows / Git Bash）**
- 复杂远端命令（引号嵌套、`$()`、循环）一律写成脚本文件 `scp` 到服务器 /tmp/ 执行，先 `sed -i 's/\r$//'` 去 CRLF
- `pkill -f 'xxx.py'` 会匹配到承载命令自身的 bash 而自杀：模式里用 `[.]` 规避（如 `app[.]py --dev`）
- ssh 远端 `nohup ... &` 常驻服务不可靠（会话回收即死），一律 systemd（Dev 也要装，仿 pwpanel-dev.service）

**容器内跑 node（LibreChat 镜像）**
- 脚本 docker cp 进容器 /tmp/ 后 `require('mongodb')` 解析不到：必须绝对路径 `require('/app/node_modules/mongodb')`
- 容器进程以 uid 1000 运行：docker cp 进去的文件若 600 会 EACCES，先 `chmod 644`
- `docker exec` 默认继承容器 ENV，`process.env.MONGO_URI` 直接可用，Dev/生产同一份代码自动连各自库

**LibreChat v0.8.8-rc4 特性**
- **access token 只存在 SPA 内存**，localStorage/sessionStorage/cookie 都拿不到；前端补丁**绝不要调 `/api/auth/refresh`**——它是轮换式，会顶掉 SPA 自己的凭据导致用户被登出（唯一例外：注销账户场景，本来就要登出）
- `GET /api/user` 的响应被 schema 过滤，**自定义字段（如 mustChangePassword）带不出来**；要前端可读就得自建查询接口
- ADMIN 角色在 UI 上**没有任何可见特征**（菜单与 USER 完全一致），前端判断身份用不了 role——用配置白名单（lc_custom.js 的 `USAGE_ADMINS`）或登录时捕获的邮箱
- 没有"登录后改密码"功能（只有邮件重置且未配 SMTP）；自助改密/删号走自建服务
- 登录按钮 `type=button`，原生 submit 事件不触发；补丁监听 document 捕获阶段 click/Enter 抓登录表单值
- 内置删除接口 `DELETE /api/user/delete` 删的是**当前会话用户**，不是"表单里填的用户"——任何删除/敏感操作必须先校验会话身份与用户输入一致（曾因此误删 Dev 账号）
- 内置"注销"菜单=退出登录；自建"注销账户"=删号，两者菜单文案必须区分
- **界面语言简繁并存**：简中"注销"、繁中"登出"（LibreChat 繁中把 logout 译作登出，不含注销字样）——菜单匹配/改名必须覆盖 注销|註銷|登出|退出账户|Log out；Dev 是简中界面，繁中路径要用构造 DOM 的方式单独验证
- **MutationObserver 自毁循环**：注入节点/改名本身会再触发 Observer——若"已存在检查"只认旧特征（改名后的项不再匹配）或存在清理逻辑删掉刚注入的节点，会出现"第一次成功、之后永远失败/注入即消失"；幂等判据必须兼容自己改过后的状态，禁止移除非本容器的节点

**前端补丁（lc_custom.js）**
- 双模式单文件：浏览器经 nginx `/lc_custom.js`（no-cache）加载；段=SECTIONS 数组，`String.raw` 包裹，**段内禁用反引号和 `${`**
- 改任何段内容必须 PATCH_VERSION +1（这是用户看到的版本号，deploy 脚本写进 /picasso-version.txt，老页面 60 秒内弹更新）
- 脚本元素被抽出来重建执行，其余元素 append 到 body；SPA 路由会重建 React DOM——插入的节点要 MutationObserver 重插
- 登录态邮箱来源：登录表单捕获（key `lc-user-email`）+ 头像菜单内 `[role="note"]` 的邮箱（老会话兜底）；IAB 浏览器对部分按钮 role 定位会卡超时，改用 `evaluate` 直接 DOM 操作

**服务与脚本**
- 零依赖优先：Python stdlib http.server + `docker exec`（仿 usagepanel/pwpanel），不引 Flask/pymongo
- 防爆破：登录类接口必须限速（pwpanel：同邮箱错 5 次锁 15 分钟）；错误信息不泄露账号是否存在
- 幂等：建号/改配置脚本重跑不重复不炸；nginx 改动备份 + `nginx -t` 不过自动还原

## 4. 发布前检查清单

- [ ] Dev 上 API + 数据 + UI 三层验证过（含错误场景）
- [ ] 该停的地方停了：**明确问了用户"要不要上生产"并得到肯定答复**
- [ ] 生产操作影响面已知：零重启（补丁）？reload nginx（毫秒）？容器/网关重启（打断用户，需低峰+确认）？
- [ ] 敏感信息没进 git/没上传外部服务
- [ ] 生产验证做完 + 《部署清单.md》更新 + commit + `live-YYYYMMDD` tag 已推
