# 部署指南 · Deployment Guide

本文覆盖三条路径：① 在 **Windows 本地**用 Docker 跑起来；② 把项目**推到 GitHub**并启用 Actions 自动测试/构建；③ 用 GitHub 构建出的镜像**部署到服务器**。
This guide covers three paths: ① run it locally on **Windows** with Docker; ② push to **GitHub** and enable Actions for CI/build; ③ **deploy to a server** using the images GitHub builds.

---

# 中文版

## 0. 总览

| 路径 | 适合 | 命令入口 |
|------|------|----------|
| 本地体验 | 自己电脑（Windows）跑全套 | `docker compose up --build` |
| GitHub CI/CD | 推代码后自动测试、构建镜像 | `.github/workflows/` 自动触发 |
| 服务器部署 | 拉 GHCR 镜像上线 | `docker-compose.prod.yml` |

## 1. 准备（Windows）

1. 安装 **Docker Desktop**，安装时勾选 **WSL2 后端**（Settings → General → Use WSL2）。
2. 安装 **Git for Windows**。
3. 关键一步——避免换行符问题：

   ```powershell
   git config --global core.autocrlf input
   ```

   本项目自带 `.gitattributes` 强制用 LF，但建议同时设上面这行。**原因**：Windows 上 Git 默认把文件检出成 CRLF，容器是 Linux，`.sh`/启动命令带了 `\r` 会报 `command not found` 或 `no such file`。

## 2. 本地用 Docker Compose 跑

在 PowerShell 里进入项目根目录：

```powershell
copy .env.example .env          # 首次运行，按需改端口
docker compose up --build
```

启动后：

- 前端 <http://localhost:3000>
- 后端文档 <http://localhost:8000/docs>

四个容器：`redis`（队列）、`backend`（API）、`worker`（ARQ 训练）、`frontend`（Nuxt）。

常用命令：

```powershell
docker compose ps                 # 看状态
docker compose logs -f worker     # 跟踪某个服务日志
docker compose up -d --scale worker=3   # 多开 3 个训练 worker
docker compose down               # 停止（加 -v 连数据卷一起删）
```

> 数据持久化在命名卷 `dao-data`（模型/数据集）和 `redis-data`（队列）。`docker compose down` 默认保留卷，加 `-v` 才清空。

## 3. 推到 GitHub

```powershell
git init
git add .
git commit -m "init: Data Observatory"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

`.gitignore` 已排除 `node_modules/`、`.env`、`backend/var/` 等，**密钥不会被提交**。

## 4. GitHub Actions（自动测试 + 构建镜像）

推送后，仓库的 **Actions** 标签页会出现两个流程：

### CI（`.github/workflows/ci.yml`）
每次 push / PR 自动运行：

- **backend**：起一个 Redis service container，装依赖，跑 `pytest`（含纯流程冒烟 + ARQ×Redis 集成测试）。
- **frontend**：`npm install` + `npm run build`，验证 Nuxt 能完整构建。

### Deploy（`.github/workflows/deploy.yml`）
push 到 `main` 或打 `v*` 标签时：

- 构建 `backend` / `frontend` 两个镜像，推送到 **GHCR**（GitHub Container Registry，`ghcr.io/<owner>/data-observatory-*`）。
- 自动打标签：分支名、语义化版本（来自 `v*` tag）、短 commit SHA、`latest`（默认分支）。

**无需额外配置密钥**：用的是内置的 `GITHUB_TOKEN`。首次推送后，去 GitHub → 你的头像 → Packages 能看到镜像。**默认是 private**，服务器拉取需要登录（见第 5 步），或在该 package 的 Settings 里把可见性改为 Public。

## 5. 部署到服务器

服务器需装好 Docker + Docker Compose。把仓库克隆（或只拷 `docker-compose.yml`、`docker-compose.prod.yml`、`.env`）到服务器，然后：

```bash
# 1) 登录 GHCR（若镜像是 private）
echo <你的GitHub PAT> | docker login ghcr.io -u <你的用户名> --password-stdin

# 2) 指定镜像来源
export REGISTRY=ghcr.io/<你的用户名或组织>
export IMAGE_TAG=latest          # 或具体版本 v1.0.0

# 3) 准备 .env（重点改 PUBLIC_API_BASE 为服务器公网地址）
cp .env.example .env
#   PUBLIC_API_BASE=http://<服务器IP或域名>:8000
#   DAO_CORS_ORIGINS=["http://<服务器IP或域名>:3000"]

# 4) 拉镜像并起服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-build
```

> PAT（个人访问令牌）：GitHub → Settings → Developer settings → Tokens，勾选 `read:packages` 即可拉取。

### 可选：push 后自动部署

`deploy.yml` 里已写好一个 `deploy-server` 任务，默认关闭。打开方式：

1. 仓库 Settings → Secrets and variables → Actions
2. 加 **Variables**：`ENABLE_DEPLOY = true`
3. 加 **Secrets**：`DEPLOY_HOST`（服务器 IP）、`DEPLOY_USER`、`DEPLOY_SSH_KEY`（私钥）、`DEPLOY_PATH`（服务器上 compose 文件所在目录）

之后每次 push 到 main，Actions 构建完镜像会自动 SSH 到服务器 `pull` + `up -d`。

## 6. 常见问题

- **容器内报 `\r` / `command not found`**：CRLF 问题，回到第 1 步设 `core.autocrlf input` 后重新 clone。
- **端口被占用**：改 `.env` 里的 `BACKEND_PORT` / `FRONTEND_PORT`。
- **前端能打开但训练报连不上后端**：检查 `.env` 的 `PUBLIC_API_BASE`，部署到服务器时必须是公网可达地址，不能是 `localhost`。
- **跨域 CORS 报错**：把前端地址加进 `DAO_CORS_ORIGINS`。
- **worker 不消费任务**：确认 `worker` 容器在跑且 `DAO_REDIS_DSN` 与 backend 一致；`docker compose logs worker` 看日志。
- **拉镜像 401/denied**：GHCR 镜像是 private，需先 `docker login ghcr.io` 或把 package 改 Public。

---

# English

## 0. Overview

| Path | For | Entry |
|------|-----|-------|
| Local | Run everything on your machine (Windows) | `docker compose up --build` |
| GitHub CI/CD | Auto test & build images on push | `.github/workflows/` |
| Server | Ship GHCR images to production | `docker-compose.prod.yml` |

## 1. Prerequisites (Windows)

1. Install **Docker Desktop** with the **WSL2 backend** enabled (Settings → General → Use WSL2).
2. Install **Git for Windows**.
3. Critical — avoid line-ending issues:

   ```powershell
   git config --global core.autocrlf input
   ```

   The repo ships `.gitattributes` forcing LF, but set the above too. **Why**: Git on Windows checks files out as CRLF by default; the containers are Linux, and a `\r` in shell/startup commands causes `command not found` / `no such file`.

## 2. Run locally with Docker Compose

From the project root in PowerShell:

```powershell
copy .env.example .env          # first run; adjust ports as needed
docker compose up --build
```

Then open:

- Frontend <http://localhost:3000>
- Backend docs <http://localhost:8000/docs>

Four containers: `redis` (queue), `backend` (API), `worker` (ARQ training), `frontend` (Nuxt).

Handy commands:

```powershell
docker compose ps
docker compose logs -f worker
docker compose up -d --scale worker=3
docker compose down            # add -v to also delete data volumes
```

> Data persists in the named volumes `dao-data` (models/datasets) and `redis-data` (queue). `docker compose down` keeps volumes unless you pass `-v`.

## 3. Push to GitHub

```powershell
git init
git add .
git commit -m "init: Data Observatory"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

`.gitignore` already excludes `node_modules/`, `.env`, `backend/var/`, etc. — **secrets are never committed**.

## 4. GitHub Actions (auto test + image build)

After pushing, the repo's **Actions** tab shows two workflows:

### CI (`.github/workflows/ci.yml`)
Runs on every push / PR:

- **backend**: spins up a Redis service container, installs deps, runs `pytest` (pure-pipeline smoke + ARQ×Redis integration tests).
- **frontend**: `npm install` + `npm run build` to verify a full Nuxt build.

### Deploy (`.github/workflows/deploy.yml`)
On push to `main` or a `v*` tag:

- Builds the `backend` / `frontend` images and pushes them to **GHCR** (`ghcr.io/<owner>/data-observatory-*`).
- Auto-tags: branch name, semantic version (from `v*` tags), short commit SHA, and `latest` (default branch).

**No extra secrets needed** — it uses the built-in `GITHUB_TOKEN`. After the first push, find the images under GitHub → your avatar → Packages. They are **private by default**; a server needs to log in to pull (step 5), or you can set the package visibility to Public.

## 5. Deploy to a server

The server needs Docker + Docker Compose. Clone the repo (or just copy `docker-compose.yml`, `docker-compose.prod.yml`, `.env`) to it, then:

```bash
# 1) Log in to GHCR (if images are private)
echo <your GitHub PAT> | docker login ghcr.io -u <you> --password-stdin

# 2) Point at the image source
export REGISTRY=ghcr.io/<your-name-or-org>
export IMAGE_TAG=latest          # or a specific version, e.g. v1.0.0

# 3) Prepare .env (set PUBLIC_API_BASE to the server's public address)
cp .env.example .env
#   PUBLIC_API_BASE=http://<server-ip-or-domain>:8000
#   DAO_CORS_ORIGINS=["http://<server-ip-or-domain>:3000"]

# 4) Pull and start
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-build
```

> PAT (Personal Access Token): GitHub → Settings → Developer settings → Tokens, with `read:packages` scope is enough to pull.

### Optional: auto-deploy on push

`deploy.yml` already includes a `deploy-server` job, disabled by default. To enable:

1. Repo Settings → Secrets and variables → Actions
2. Add **Variable**: `ENABLE_DEPLOY = true`
3. Add **Secrets**: `DEPLOY_HOST` (server IP), `DEPLOY_USER`, `DEPLOY_SSH_KEY` (private key), `DEPLOY_PATH` (dir with the compose files on the server)

Then every push to main builds the images and SSHes into the server to `pull` + `up -d`.

## 6. Troubleshooting

- **`\r` / `command not found` inside a container**: CRLF issue — set `core.autocrlf input` (step 1) and re-clone.
- **Port already in use**: change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`.
- **Frontend loads but training can't reach the backend**: check `PUBLIC_API_BASE` in `.env`; on a server it must be a publicly reachable address, not `localhost`.
- **CORS errors**: add the frontend URL to `DAO_CORS_ORIGINS`.
- **Worker not consuming jobs**: confirm the `worker` container is up and its `DAO_REDIS_DSN` matches the backend; check `docker compose logs worker`.
- **401/denied pulling images**: GHCR images are private — `docker login ghcr.io` first, or set the package to Public.
