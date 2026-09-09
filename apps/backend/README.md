# apps/backend

FastAPI 标准后端，提供业务中立的认证、授权、审计和运行基础设施。

## 技术栈

- FastAPI + SQLAlchemy 2.0 async + Alembic
- PostgreSQL + Redis
- Pydantic v2 + Loguru
- uv 包管理

## 本地启动

```powershell
uv python install 3.14
uv python pin 3.14
uv sync --locked
uv run python -c "import sys; assert sys.version_info[:2] == (3, 14); print(sys.version)"
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8100
```

本项目使用 uv 管理 Python 版本、项目 `.venv`、依赖和命令运行，不要求激活 Conda 环境。环境变量职责、VS Code 工作区和后端启动顺序见[环境变量分层与 Backend 本地运行手册](../../docs/operations/environment-variables-and-backend-local-run.md)，完整的 Windows 环境、PostgreSQL 和 Docker Desktop Redis 初始化见[本地开发环境手册](../../docs/operations/local-dev-environment.md)。

## 环境变量

复制 `apps/backend/.env.example` 为 `apps/backend/.env` 并填入本地配置。真实 `.env` 不得提交到仓库。

## 当前范围

当前已实现配置、请求上下文、统一错误响应、数据库会话与事务、Redis 生命周期、Alembic、健康探针和 `system` 状态接口，以及 Browser Cookie 认证、用户、管理员、RBAC、Session/Refresh、CSRF、限流、安全事件、审计和可选请求元数据管道。

母版不包含 CMS、电商等具体业务领域。派生仓库通过 `app/domains/` 的公开入口和 `app/services/` 编排层按计划扩展。

## 质量检查

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run lint-imports
uv run pytest tests/ -v
```

数据库集成测试必须显式配置独立的 `TEST_DATABASE_URL` 和 `TEST_REDIS_URL`，数据库名以 `_test` 结尾。
