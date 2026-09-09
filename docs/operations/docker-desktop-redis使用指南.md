# Docker Desktop Redis 使用指南

> 文档归属：`docs/operations/docker-desktop-redis使用指南.md`
> 适用仓库：`pinjie-fullstack-blog` 及其派生项目
> 架构决策：[ADR 0003：本地开发环境架构决策](../adr/0003-本地开发环境架构决策.md)；[ADR 0010：浏览器认证会话RBAC与审计决策](../adr/0010-浏览器认证会话RBAC与审计决策.md)
> 延伸阅读：[Windows 本地开发环境手册](local-dev-environment.md)；[环境变量分层与 Backend 本地运行手册](environment-variables-and-backend-local-run.md)

---

## 一、架构设计与本地选型背景

在 Windows 本地全栈开发中，本项目采用“本机应用进程 + 本机 PostgreSQL + Docker Desktop Redis”的混合开发架构：

```text
Windows 本机开发拓扑
├── Backend：uv + CPython 3.14 + FastAPI（端口 8100）
├── Admin：pnpm + Umi Max + React 19 + Ant Design 6（端口 3101）
├── Web：pnpm + Next.js 15（端口 3100）
├── PostgreSQL：Windows 本机服务（端口 5432）
└── Docker Desktop
    └── Redis 8.10.0-alpine：单容器 + 命名数据卷持久化（端口 6379）
```

### 1. 为什么本地 Redis 选择 Docker 容器化

- **零污染 Windows 宿主系统**：Redis 官方早已停止维护原生 Windows 编译版本，使用官方 Linux Alpine 容器镜像是最稳定、与生产最一致的方式。
- **免去环境编译与依赖包冲突**：通过标准 Docker 镜像实现开箱即用，避免本地缺失 C++ 运行库或服务注册异常。
- **数据卷独立可控**：通过 Docker 命名数据卷（Named Volume）实现数据安全持久化，日常重启电脑不会丢失登录 Session 与测试缓存。
- **极低系统资源占用**：`redis:8.10.0-alpine` 镜像体积仅约 118 MB，日常运行内存仅占用 15~30 MB，对本地电脑性能无感知。

---

## 二、Docker Desktop Redis 快速上手

### 1. 前置条件

1. 确保已安装并启动 **Docker Desktop**（左下角显示 `Engine running` 绿色状态）。
2. 在 PowerShell 中确认 Docker 可用：

```powershell
docker --version
docker compose version
```

### 2. 命令行日常启动与停止

本项目根目录已提供极简的 `compose.yml` 配置文件。所有操作均在**仓库根目录**执行：

- **后台启动 Redis**：

```powershell
docker compose up -d redis
```

- **检查容器运行状态**：

```powershell
docker compose ps
```

- **探活与连通性测试（Ping）**：

```powershell
docker compose exec redis redis-cli ping
```

返回 `PONG` 即表示 Redis 服务完全就绪。

- **查看 Redis 实时运行日志**：

```powershell
docker compose logs -f redis
```

- **正常停止 Redis（保留数据）**：

```powershell
docker compose stop redis
```

- **停止并移除容器（仍保留数据卷）**：

```powershell
docker compose down
```

- **彻底重置并清空所有 Redis 数据（高危操作，会删除数据卷）**：

```powershell
docker compose down -v
```

### 3. Docker Desktop 界面可视化操作

除命令行外，也可以在 Docker Desktop 图形界面中完成全生命周期管理：

- **查看容器**：在左侧 **Containers** 菜单中，可直接查看名为 `pinjie-fullstack-blog-redis-1` 的容器状态、端口映射（`0.0.0.0:6379->6379/tcp`）、实时 CPU/内存占用。
- **一键启停**：点击容器列表右侧的 **Start / Stop / Restart** 按钮。
- **查看日志与终端**：点击容器名称进入详情页，切换 **Logs** 查看 Redis 实时日志，切换 **Exec** 可直接在网页端输入 `redis-cli` 交互执行命令。
- **管理数据卷**：在左侧 **Volumes** 菜单中，可查看 `redis_data` 卷的大小与挂载状态。

---

## 三、本项目中 Redis 的集成现状与关键职责

在 `pinjie-fullstack-blog` 中，Redis 不仅仅是普通缓存，更是**阶段 C 核心安全与会话控制的关键依赖**（Fail-Closed 模式）：

```text
Backend 安全子系统对 Redis 的依赖矩阵
├── 会话活跃状态追踪（Active Session Tracker）
├── 凭据版本与 Refresh Token 轮换防重放
├── 主动注销与会话撤销黑名单（Session Revocation）
├── 登录防暴力破解滑动时间窗口限流（Rate Limiter）
├── CSRF 双重 Cookie 防护中间件
└── 异步请求元数据日志缓冲流（Redis Stream）
```

### 1. 后端配置与环境变量绑定

在 `apps/backend/.env` 中配置 Redis 连接：

```dotenv
# Redis 安全模式：required 表示启动时强依赖，探活失败则拒绝启动
REDIS_MODE=required
REDIS_URL=redis://127.0.0.1:6381/0
```

- `REDIS_MODE=required`：在 local、test 和 production 环境下，后端启动阶段会主动执行 `redis.ping()`。若无法连接，后端会立即拒绝启动并报错，防止在无会话保护的裸奔状态下对外提供服务。
- `REDIS_URL=redis://127.0.0.1:6381/0`：指定连接博客独立 Redis 宿主 6381 端口的 **0 号数据库**。

---

## 四、多项目共存与本地数据隔离规则

博客使用独立 Compose 项目 pinjie-fullstack-blog-local 和独立数据卷，宿主绑定 127.0.0.1:6381，容器内部保持 6379。其他项目的 Redis 不参与博客本地运行。

### 1. 开发和测试隔离

| 数据库编号 | 用途 | 连接模板 |
| --- | --- | --- |
| 0 | 博客本地开发 | `REDIS_URL=redis://127.0.0.1:6381/0` |
| 15 | 博客专项测试 | `TEST_REDIS_URL=redis://127.0.0.1:6381/15` |

测试命令只有明确授权后执行，必须核验主机、端口、数据库编号及环境，不能仅凭逻辑库编号就执行清空。生产使用单独配置和凭据，不复用本机开发或测试实例。

### 2. Key 命名空间规范（统一前缀）

为保障代码在迁移到生产 Cluster（Redis 集群模式不支持多 DB，默认只用 DB 0）时的无缝兼容，所有存入 Redis 的 Key 统一采用冒号分隔的命名空间格式：

```text
{项目}:{环境}:{领域}:{用途}:v{版本}:{标识}
```

- 会话状态 Key：`pinjie:auth:session:<session_id>`
- 用户凭据版本 Key：`pinjie:auth:user_cred:<user_id>`
- 管理员登录限流 Key：`pinjie:ratelimit:admin_login:<client_ip>`
- 请求元数据 Stream Key：`pinjie:stream:request_logs`

### 3. 数据生命周期与清空操作规范

本地开发时，请根据需求区分不同的清空方式：

- **只清空当前项目的数据库（安全）**：
  进入当前项目对应的数据库编号后执行：

  ```powershell
  # 仅清空当前连接的 DB 0，不影响 DB 1、DB 2 等其他项目
  docker compose exec redis redis-cli -n 0 FLUSHDB
  ```

- **清空整台 Redis 实例的所有数据（影响全部项目）**：

  ```powershell
  # 清空 0~15 所有数据库，所有项目的本地登录态均会失效
  docker compose exec redis redis-cli FLUSHALL
  ```

---

## 五、常见问题排查与日常避坑

### 1. Docker 引擎未启动导致连接拒绝

- **现象**：执行 `docker compose up -d redis` 时报错：`error during connect: ... open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
- **解决**：打开 Windows 开始菜单，启动 **Docker Desktop** 软件，等待左下角引擎状态变为绿色的 `Engine running` 后再运行命令。

### 2. 本地 6379 端口冲突

- **现象**：启动 Redis 容器时报错：`Bind for 0.0.0.0:6379 failed: port is already allocated.`
- **原因**：本地 Windows 之前安装过 Windows 版 Redis 原生服务，或有其他容器正在占用 6379 端口。
- **排查与解决**：
  1. 在 PowerShell 中查找占用者：`Get-NetTCPConnection -LocalPort 6379 -ErrorAction SilentlyContinue`
  2. 若存在本地已注册的 Windows Redis 服务，在 Windows 服务管理器中将其停止并设置为“手动”；
  3. 释放 6379 端口后重新执行 `docker compose up -d redis`。

### 3. 后端启动报 Redis 连接超时或连接失败

- **排查步骤**：
  1. 运行 `docker compose ps`，确认 redis 容器处于 `Up` 状态。
  2. 运行 `docker compose exec redis redis-cli ping`，确认能收到 `PONG`。
  3. 打开 `apps/backend/.env`，核对 `REDIS_URL` 是否拼写为 `redis://127.0.0.1:6381/0`，不要写成容器内部域名 `redis://redis:6379/0`（后者仅在容器网络互联时有效）。

### 4. 磁盘与构建缓存清理（节省磁盘空间）

- Docker Desktop 运行久了可能会积累一些旧镜像或 BuildKit 构建缓存。
- 可以安全运行以下命令清理多余缓存，不会删除您的 `redis:8.10.0-alpine` 镜像与数据卷：

```powershell
# 清理悬空/无用的构建缓存（保留数据卷和正在运行的容器）
docker builder prune -f

# 查看各资源占用情况
docker system df
```

---

## 六、后续演进与生产部署建议

### 1. 从本地开发走向 1Panel 生产环境

本地与生产环境的 Redis 存在以下关键演进点：

| 关注维度 | 本地开发（Docker Desktop） | 生产部署（1Panel / OpenResty / Docker Compose） |
| --- | --- | --- |
| **网络隔离** | 映射到宿主机 `localhost:6379` | 容器专有内部网络，**严禁向公网开放 6379 端口** |
| **容器互联地址** | `redis://127.0.0.1:6381/0` | `redis://:生产强密码@redis:6379/0`（使用容器服务名 `redis`） |
| **访问凭据** | 免密访问（快速开发） | 强制配置 `requirepass` 强密码认证 |
| **持久化机制** | RDB 快照 | RDB 快照 + AOF（`appendonly yes`）持久化双保险 |
| **高危命令禁用** | 开放所有命令 | 生产通过 `rename-command` 禁用 `FLUSHALL`、`FLUSHDB`、`KEYS`、`CONFIG` |
| **内存淘汰策略** | 默认 `noeviction` | 设置 `maxmemory` 上限与 `volatile-lru` / `allkeys-lru` 策略 |

### 2. 生产环境 Redis 配置参考模板

在生产 `compose.prod.yml` 或 1Panel 容器编排中，推荐采用以下标准启动参数：

```yaml
services:
  redis:
    image: redis:8.10.0-alpine
    restart: unless-stopped
    command: >
      redis-server
      --requirepass "${REDIS_PASSWORD}"
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy volatile-lru
    volumes:
      - redis_prod_data:/data
    networks:
      - internal_network

volumes:
  redis_prod_data:
```

### 3. 监控与告警指标建议

当业务进入生产阶段后，建议通过 1Panel 或 Prometheus 重点监控以下指标：

- **`used_memory` / `maxmemory`**：内存使用率，超过 80% 触发容量告警；
- **`connected_clients`**：当前连接数，异常突增排查连接池泄漏；
- **`instantaneous_ops_per_sec`**：每秒执行指令数（QPS）；
- **`keyspace_hits` / `keyspace_misses`**：缓存命中率，评估缓存设计有效性。
