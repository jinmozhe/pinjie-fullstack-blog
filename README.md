# Pinjie Fullstack Blog

个人博客全栈工程：一个管理员后台和一个公开阅读网站，采用 FastAPI、Next.js、React、pnpm 和 Turborepo。

本项目独立维护，只配置博客自己的 origin，不依赖母版目录、不追踪母版版本、不执行上游同步。项目名称与网站显示名称分别管理。

## 当前范围

博客工程独立化已完成，用户反馈本地可以启动。第二阶段已实现后台文章、分类标签、Markdown 编辑预览、图片引用保护与回收站，并提供增量迁移和生成契约；数据库升级和真实写作链路尚未自动验证。第三阶段公开文章接口与阅读页面尚未实施，后台的公开状态尚不代表访客已有阅读入口。现有通用页面继续保留。

## 技术与目录

| 目录 | 职责 |
| --- | --- |
| apps/backend | FastAPI、SQLAlchemy async、PostgreSQL、Redis、Alembic |
| apps/admin | Umi Max、React、Ant Design、ProComponents、TanStack Query |
| apps/web | Next.js App Router、React、Tailwind CSS、公开阅读网站 |
| packages | 本仓库维护的 API Client、ESLint 与 TypeScript 公共包 |
| docs | 产品、架构、决策和操作文档 |
| plans | 博客实施计划、计划规范与永久登记 |

内部 @pinjie workspace 包均从本仓库解析，与外部母版无运行依赖。

## 本地开始

按 [本地开发手册](docs/operations/local-dev-environment.md)安装锁定依赖，创建博客独立环境。真实配置、数据库密码和认证密钥不得提交。

```powershell
pnpm install --frozen-lockfile
Set-Location apps/backend
uv sync --locked
```

三端环境、初始化管理员与启动顺序见 [环境变量与 Backend 手册](docs/operations/environment-variables-and-backend-local-run.md)。本地统一使用 localhost：Web 3000、Admin 3001、Backend 8000，博客 Redis 宿主端口 6381；PostgreSQL 使用本机 5432 上的独立数据库和账号。同一时刻启动多个项目时需调整冲突端口。生产沿用容器内部端口，各项目分配不同宿主映射端口，再由域名反代分流。

已有本地环境启用文章后台的增量迁移、权限同步和日常写作步骤见 [博客后台启用与写作](docs/operations/blog-writing.md)。

## 项目导航

- [项目身份与活动计划](PROJECT_INDEX.md)
- [博客需求与验收](docs/PROJECT_REQUIREMENTS.md)
- [计划规范](plans/README.md)与[计划登记](plans/INDEX.md)
- [文档索引](docs/README.md)
- [独立维护决策](docs/adr/0016-博客独立工程与维护边界决策.md)
- [变更记录](CHANGELOG.md)与[安全规则](SECURITY.md)

## 开发与交付

公开契约只从 Backend 导出到根 openapi.json，再通过 pnpm generate-api 生成客户端。默认执行三端轻量检查和适用治理门禁，重型测试、构建和浏览器验证单独授权。现存计划永久保护，AI 不删除计划。

CI 保留轻量检查；博客发布目标尚未配置，原发布入口明确阻断。操作边界见 [发布与回滚](docs/operations/release-and-rollback.md)。提交、推送、发布和部署分别授权，继承的历史记录不作为博客已验证或已部署的证据。
