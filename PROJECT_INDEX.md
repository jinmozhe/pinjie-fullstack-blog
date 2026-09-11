# pinjie-fullstack-blog 项目索引

本文件是项目身份、当前阶段、活动计划和权威入口。全部实施计划的永久登记见 [plans/INDEX.md](plans/INDEX.md)。

## 项目身份

| 字段 | 当前值 |
| --- | --- |
| 项目名称 | pinjie-fullstack-blog |
| 项目角色 | 独立个人博客，一个管理员后台和一个公开阅读网站 |
| 维护方式 | 独立 Git 历史，仅配置博客 origin；不追踪母版基线或进行上游同步 |
| 当前阶段 | 第一阶段工程独立化已完成，用户反馈本地可启动；第二阶段后台写作与第三阶段公开阅读、搜索及 SEO 源码已完成，Web 已接入统一设计标准；内容迁移、真实写作与阅读验收未执行 |
| 业务范围 | Markdown 写作、文章发布隐藏与软删除恢复、分类标签、公开阅读、标题摘要搜索、基础 SEO |
| 部署状态 | 博客未发布、未部署；继承材料中的运行与验收记录不作为本项目证据 |

## 权威入口

| 事项 | 唯一来源 | 用途 |
| --- | --- | --- |
| 全仓库长期规则 | [AGENTS.md](AGENTS.md) 与三个应用级 `AGENTS.md` | 任务读取、工程边界、验证和交付规则 |
| 项目身份与阶段导航 | [PROJECT_INDEX.md](PROJECT_INDEX.md) | 项目身份、当前阶段、活动计划和权威入口 |
| 详细实现状态 | 实际源码、配置、迁移、生成契约与对应架构文档 | 判断具体能力、接口和运行机制是否已经实现 |
| 产品需求基线 | [docs/PROJECT_REQUIREMENTS.md](docs/PROJECT_REQUIREMENTS.md) | 博客用户、首版能力、非目标和验收边界 |
| Web 设计标准 | [docs/architecture/web-design-standard.md](docs/architecture/web-design-standard.md) | Web 视觉、交互、响应式与可访问性的唯一详细标准 |
| 博客内容与阅读架构 | [docs/architecture/blog-content.md](docs/architecture/blog-content.md) | 内容生命周期、匿名公开接口、搜索、服务端读取与 SEO 机制 |
| 计划规则 | [plans/README.md](plans/README.md) | 计划创建、格式、状态、完成和保护规则 |
| 计划永久登记 | [plans/INDEX.md](plans/INDEX.md) | 全部实施计划的路径、状态、结果、范围和用途 |
| 项目文档清单 | [docs/README.md](docs/README.md) | `docs/` 下全部项目文档导航 |
| 架构决策 | [docs/adr/](docs/adr/) | 长期技术取舍及其理由 |
| 架构机制 | [docs/architecture/](docs/architecture/) | 当前系统边界、认证、错误、测试和可靠性机制 |
| 开发与运维步骤 | [docs/operations/](docs/operations/) | 本地开发、发布、部署、恢复和故障处理 |
| 已交付变化 | [CHANGELOG.md](CHANGELOG.md) | 已交付能力和版本变化 |
| 安全治理 | [SECURITY.md](SECURITY.md) | 漏洞报告、安全响应和安全开发要求 |
| OpenAPI 契约 | [openapi.json](openapi.json) | 后端导出的唯一机器契约，禁止手工修改 |

## 活动计划

| 计划 | 状态 |
| --- | --- |
| [博客首版全栈实施计划](plans/2026-09-09_博客首版全栈实施计划.md) | 实施中 |
