# Milestone 2 Docker 部署验证记录

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 3 日，复验日期：2026 年 6 月 4 日

关联 WBS：`M2.11`

## 1. 验证目标

本次验证用于推进 Milestone 2 中 `M2.11 部署与环境验证`：

- 验证 Docker CLI 与 Docker Compose 是否可用。
- 验证 `docker-compose.yml` 是否可以正常解析。
- 尝试执行 `docker compose up -d --build`。
- 检查环境变量、静态资源代理、模型 key 配置和数据库路径是否能进入容器配置。

## 2. 已完成检查

| 检查项 | 命令 | 结果 |
|---|---|---|
| Docker CLI | `docker --version` | PASS，Docker CLI 可用 |
| Docker Compose | `docker compose version` | PASS，Docker Compose 可用 |
| Compose 配置解析 | `docker compose config` | PASS，配置可解析 |
| Docker daemon 复验 | `docker info --format '{{.ServerVersion}}'` | PARTIAL，提权后曾返回 `29.4.3` |
| Docker Hub 拉取通道 | `docker pull hello-world:latest` | PASS，基础镜像拉取通道可用 |
| 前端镜像构建 | `PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" docker compose up -d --build` | PARTIAL，前端镜像构建成功 |
| 服务构建与启动 | `docker compose up -d --build` | BLOCKED，后端镜像构建阶段 Debian apt 下载 EOF |
| 后端 apt 稳定性缓解 | `Dockerfile.backend` | 已加入 `APT_RETRIES=5` 和 apt HTTP/HTTPS 超时参数，待 Docker 环境复验 |

## 3. 已确认的 Compose 配置

`docker compose config` 可以正常解析 `backend` 和 `frontend` 两个服务：

- `backend`
  - 使用 `Dockerfile.backend`
  - 暴露 `8000:8000`
  - 挂载 `outputs`、`logs`、`data/uploads`
  - 读取 `.env` 并设置 `HOST`、`PORT`、`ENABLE_QWEN_API`、`QWEN_MODEL`、`QWEN_BASE_URL`
- `frontend`
  - 使用 `frontend/Dockerfile`
  - 依赖 `backend`
  - 暴露 `8080:80`

安全说明：`docker compose config` 会展开 `.env` 中的真实 API key。本报告只记录配置项是否可解析，不记录任何敏感 key 值。

## 4. 阻塞点与复验记录

### 4.1 2026 年 6 月 3 日

执行：

```bash
docker compose up -d --build
```

失败信息摘要：

```text
failed to connect to the docker API at unix:///Users/mac/.docker/run/docker.sock
connect: no such file or directory
```

随后尝试启动 Docker Desktop：

```bash
open -a Docker
```

继续检查 Docker daemon：

```bash
docker info --format '{{.ServerVersion}}'
```

仍无法连接 Docker socket，说明当前环境中 Docker daemon 未完全启动或不可访问。

### 4.2 2026 年 6 月 4 日复验

基础命令：

```bash
docker --version
docker compose version
docker compose config --services
```

结果：

```text
Docker version 29.5.0, build 98f1464960
Docker Compose version v5.1.3
backend
frontend
```

尝试启动 Docker Desktop：

```bash
open -a Docker
```

随后普通沙箱环境访问 daemon 得到：

```text
permission denied while trying to connect to the docker API at unix:///Users/mac/.docker/run/docker.sock
```

使用提权命令确认 daemon 曾短暂可达：

```bash
docker info --format '{{.ServerVersion}}'
```

结果：

```text
29.4.3
```

继续执行：

```bash
docker compose up -d --build
```

首次进入 build 阶段，但在前端基础镜像元数据阶段失败：

```text
Image ppt-smart-chart-generator-frontend Building
Image ppt-smart-chart-generator-backend Building
load metadata for docker.io/library/node:20-alpine
target frontend: failed to receive status: rpc error: code = Unavailable desc = error reading from server: EOF
```

随后重试：

```bash
docker compose up -d --build
```

Docker socket 再次不可用：

```text
unable to get image 'ppt-smart-chart-generator-backend':
failed to connect to the docker API at unix:///Users/mac/.docker/run/docker.sock
connect: no such file or directory
```

最终状态确认：

```bash
docker info --format '{{.ServerVersion}}'
docker compose ps
```

均返回 socket 不存在，未发现容器保持运行。

### 4.3 2026 年 6 月 4 日二次复验

在 Docker Desktop 再次启动后，Docker daemon 可达：

```bash
docker info --format '{{.ServerVersion}} {{.OSType}}/{{.Architecture}}'
```

结果：

```text
29.4.3 linux/aarch64
```

首次执行 Compose 构建时发现新的环境问题：

```text
error getting credentials - err: exec: "docker-credential-desktop": executable file not found in $PATH
```

排查确认 credential helper 存在于 Docker Desktop 应用目录：

```text
/Applications/Docker.app/Contents/Resources/bin/docker-credential-desktop
```

因此使用临时 PATH 复验：

```bash
PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" docker compose up -d --build
```

本次复验新增通过项：

- credential helper 可以被找到，Docker Hub 授权阶段不再因 PATH 失败。
- `docker pull hello-world:latest` 成功。
- `frontend` 镜像完成 `npm ci`、`npm run build`、Nginx stage 和 image export。

前端构建日志摘要：

```text
RUN npm ci
added 51 packages

RUN npm run build
39 modules transformed
built in 558ms

naming to docker.io/library/ppt-smart-chart-generator-frontend:latest done
```

当前剩余阻塞点在后端镜像构建的 Debian apt 安装阶段：

```text
RUN apt-get update && apt-get install -y --no-install-recommends gcc libgomp1 curl
E: Failed to fetch http://deb.debian.org/debian/pool/main/b/binutils/libbinutils_2.44-3_arm64.deb
500 writing response to deb.debian.org:80: reading HTTP GET: unexpected EOF
E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?
target backend: failed to solve
```

本轮结论：Docker daemon 和 Docker Hub 基础拉取已可用；前端容器镜像已能成功构建；后端镜像因 Debian apt 下载 EOF 未完成，因此 Compose 仍未进入双容器运行与 Nginx 代理验证阶段。

### 4.4 Dockerfile 稳定性缓解

根据 4.3 中的失败点，已在 `Dockerfile.backend` 中将后端 apt 阶段改为可重试执行：

```dockerfile
ARG APT_RETRIES=5

RUN set -eux; \
    apt-get -o Acquire::Retries="${APT_RETRIES}" \
        -o Acquire::http::Timeout=30 \
        -o Acquire::https::Timeout=30 \
        update; \
    apt-get -o Acquire::Retries="${APT_RETRIES}" \
        -o Acquire::http::Timeout=30 \
        -o Acquire::https::Timeout=30 \
        install -y --no-install-recommends gcc libgomp1 curl; \
    rm -rf /var/lib/apt/lists/*
```

说明：该改动不改变后端运行依赖，只降低 Debian apt 临时网络 EOF 对构建的影响。由于本次没有重新执行完整 Docker build，`M2.11` 状态仍保持 BLOCKED / 待复验。

## 5. 当前结论

- Docker CLI 和 Docker Compose 已安装且命令可用。
- `docker-compose.yml` 可以正常解析，前后端服务、端口、挂载和环境变量配置结构有效。
- Docker daemon 在 2026 年 6 月 4 日复验中可达，Docker Hub `hello-world` 镜像可拉取。
- 当前阻塞点已从“未进入构建 / Docker socket 不稳定”推进到“前端镜像构建成功，后端镜像 Debian apt 下载 EOF”。
- `Dockerfile.backend` 已加入 apt 重试和超时参数，等待下一轮完整 Compose 构建验证。
- 容器实际构建与启动尚未完成，`M2.11` 不能标记为已完成。

## 6. 补验证步骤

Docker Desktop 完全启动后，按顺序执行：

```bash
docker info --format '{{.ServerVersion}}'
PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" docker compose up -d --build
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8080
docker compose logs --tail=80 backend
docker compose logs --tail=80 frontend
docker compose down
```

验收通过条件：

- `docker compose up -d --build` 成功。
- `backend` 和 `frontend` 容器状态为 running。
- `http://127.0.0.1:8000/api/health` 返回 `status=ok`。
- `http://127.0.0.1:8080` 返回前端页面。
- `/api` 和 `/assets` 代理由前端 Nginx 转发到后端。

建议：如果加入 apt retry 后仍继续出现 EOF，可在后续复验中先尝试更稳定网络或为 Docker daemon 配置可用镜像/代理；不要把网络下载失败误标为业务功能通过。
