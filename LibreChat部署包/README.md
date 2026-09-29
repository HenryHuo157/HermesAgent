# LibreChat 部署包（自取）

来源：47.243.79.144 线上同款配置。**包内没有密钥，密钥要填自己的。**

## 先想清楚你要哪种

| 场景 | 你需要准备 | 看哪节 |
|---|---|---|
| A. 只是想用公司的 AI | 什么都不用装 | 直接浏览器开 https://47.243.79.144 注册 |
| B. 在自己电脑/服务器跑一套，普通聊天 | 任意机器 + Docker | 第三节 + 用 librechat.yaml 里的「OpenRouter 直连」段（填你自己的 sk-or-v1- 开头 Key） |
| C. 完整复刻公司这套（AI 能在沙盒执行命令/跑代码/生成文件） | 一台 Linux 服务器 + 部署 Hermes Agent | 第三节 + 第五节，librechat.yaml 用「Hermes」段 |

## 一、文件说明

- `docker-compose.yml` — 启动 LibreChat + MongoDB（已是最精简版，只有这两个容器）
- `librechat.yaml` — 后端对接配置（两个模板段：Hermes / OpenRouter 直连，用哪个留哪个）
- `.env.example` — 复制为 `.env` 后改两处：HOST 改 0.0.0.0、SECRET_KEY 换成随机值

## 二、准备

1. 装好 Docker 和 compose 插件：
   - Linux：`dnf install -y docker && systemctl enable --now docker && dnf install -y docker-compose-plugin`
   - Windows/Mac：装 Docker Desktop 即可
2. 把本文件夹整体拷到目标机器，比如 `~/lc/`

## 三、启动

```bash
cd ~/lc
cp .env.example .env        # 然后编辑：SECRET_KEY 换成 `openssl rand -hex 32` 的输出
nano librechat.yaml         # 选好后端段，填自己的 API Key
docker compose up -d
# 等 30 秒，然后浏览器打开 http://localhost:3080
# 第一个注册的账号自动成为管理员
```

常用命令：
```bash
docker compose restart      # 重启
docker compose logs -f api  # 看日志
docker compose down         # 停止
```

## 四、给团队用（可选）

默认只有本机能访问。要给别人用，需要：一台有公网 IP 的服务器 + 域名 + HTTPS 证书（Caddy 免费自动证书最省事），
把 docker-compose.yml 里 api 的 ports 改成 `127.0.0.1:3080:3080`，前面挂反代。参考公司线上的 nginx 配置。

## 五、场景 C：部署 Hermes Agent（AI 的大脑）

1. 最快路径：阿里云轻量服务器直接选「Hermes Agent 0.20.0」应用镜像（公司这台就是这么来的）
2. 装好后开启 API：
   ```bash
   hermes config set API_SERVER_ENABLED true
   hermes config set API_SERVER_KEY $(openssl rand -hex 24)
   hermes gateway restart
   ```
3. 把 librechat.yaml「Hermes」段的 baseURL 改成 `http://<你的服务器IP>:8642/v1`，apiKey 填上面的 KEY
4. 安全提示：8642 会对公网开放，务必确认 Key 足够强；更稳妥的做法是只放行 LibreChat 所在机器的 IP（防火墙/安全组）

## 六、密钥安全（务必读）

- 不要把填了真实 Key 的 librechat.yaml / .env 传回共享盘或提交到 git
- 各用各的 Key：账单各自独立，谁也不用替谁付
- 公司线上那台（47.243.79.144）的 Key 不外传；同事要用公司的 AI，走场景 A 注册账号即可
