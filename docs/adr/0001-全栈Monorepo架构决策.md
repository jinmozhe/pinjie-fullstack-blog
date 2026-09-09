# ADR 0001: 全栈 Monorepo 架构决策

- 状态：已确认
- 日期：2026-08-10
- 决策者：大仙
- 原始方案参考：[全栈Monorepo架构规划原始方案.md](../architecture/全栈Monorepo架构规划原始方案.md)

## 背景

需要一个通用全栈项目母版，同时支持 B 端管理后台和 C 端用户前端，可用于博客、CMS、企业站、管理平台、电商等项目的初始化和二次开发。

## 决策

采用 pnpm workspace Monorepo 模式，将后端和多个前端应用组织在同一仓库中。

## 目录约定

```text
apps/backend   FastAPI 后端（Python / uv）
apps/web       C 端用户前端（Next.js）
apps/admin     B 端管理前端（Ant Design Pro v6 / Umi Max）
packages/      共享包（api-client、eslint-config、typescript-config）
docs/          项目知识库（ADR、架构设计、运营手册、业务蓝图）
plans/         实施计划文档
openapi.json   后端导出的 OpenAPI 规范（根目录，前端 SDK 生成唯一来源）
```

Admin 的当前实现基线由 [ADR 0011：Admin 采用 Ant Design Pro v6 与 Umi Max](0011-Admin采用AntDesignProV6与UmiMax决策.md) 定义，包括 `@umijs/max` 配置式路由、运行时 `src/app.tsx`、ProLayout、Access 和 Ant Design 6。本文的 Monorepo 目录决策仍然有效。

## 共享边界规则

- `apps/web` 和 `apps/admin` 之间禁止直接互相引用业务实现
- 两个前端只共享 `packages/api-client`（自动生成）、`packages/eslint-config`、`packages/typescript-config`
- `openapi.json` 在根目录，是前端唯一的接口类型来源，禁止手改

## 通用母版边界

母版 `apps/` 只包含以下通用能力：

- 后端：auth、users、admin（RBAC）、system 四个领域
- Web 前端：auth、user 两个 feature
- Admin 前端：login、dashboard、system 三个页面

业务扩展（电商、CMS、博客等）通过 `docs/blueprints/` 蓝图文档说明，不放入母版代码。

## 代价与风险

- 构建时间：多应用并行构建，需要 turbo 加速
- 工具链：Python 用 uv，JavaScript 用 pnpm，两套包管理工具并存
- 权限边界：需要在 CI lint 规则中防止跨域直接引用
