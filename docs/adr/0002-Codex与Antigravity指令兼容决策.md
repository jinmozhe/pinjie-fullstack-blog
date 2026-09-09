# ADR 0002: Codex 与 Antigravity 项目指令兼容决策

- 状态：已确认
- 日期：2026-08-10
- 决策者：大仙
- 适用范围：`pinjie-fullstack-base` 仓库及其派生项目

## 背景

本项目主要使用 ChatGPT 桌面客户端中的 Codex 和 Google Antigravity 进行本地开发。两套工具的项目指令发现机制不同：

- Codex 原生读取 `AGENTS.md`，并按照项目根目录到当前工作目录的顺序合并指令。
- Antigravity 的全局规则位于 `~/.gemini/GEMINI.md`，项目级 Workspace Rules 位于 `.agents/rules/`。
- Antigravity 支持在 Rule 中使用 `@文件路径` 引用其他 Markdown 文件，并支持 Always On、Glob、Model Decision 和 Manual 激活方式。

如果分别在 `AGENTS.md` 和 `.agents/rules/` 中维护完整规则，长期会产生内容重复、更新遗漏和规则冲突。仅依赖个人全局配置要求 Antigravity 主动查找 `AGENTS.md`，又会使项目失去随仓库迁移和共享的能力。

## 决策目标

1. 项目规则只有一份正文来源。
2. Codex 和 Antigravity 都通过各自官方机制稳定加载规则。
3. 后端、管理端和用户端按目录应用各自规则。
4. 项目规则随仓库进入版本控制，不依赖某台电脑的个人配置。
5. 个人偏好与项目规则分离，避免污染其他项目。

## 决策

采用“`AGENTS.md` 保存规则正文，`.agents/rules/` 负责 Antigravity 路由”的兼容方案。

目标目录结构如下：

```text
pinjie-fullstack-base/
├── AGENTS.md
├── apps/
│   ├── backend/
│   │   └── AGENTS.md
│   ├── admin/
│   │   └── AGENTS.md
│   └── web/
│       └── AGENTS.md
└── .agents/
    ├── rules/
    │   ├── 00-repository.md
    │   ├── 10-backend.md
    │   ├── 20-admin.md
    │   └── 30-web.md
    └── skills/                     # 有实际可复用技能时再创建
```

本 ADR 只确认文件职责和加载方案。各规则文件的具体内容在后续规则编写任务中创建和确认。

## 规则正文职责

| 文件 | 职责 |
| --- | --- |
| `/AGENTS.md` | 项目定位、Monorepo 边界、通用编码规则、文件格式、安全红线、生成文件、验证和交付要求 |
| `/apps/backend/AGENTS.md` | FastAPI 分层、Service 事务边界、SQLAlchemy async、Alembic、Ruff、Mypy 和 Pytest 规则 |
| `/apps/admin/AGENTS.md` | Ant Design Pro v6/Umi Max、React、TypeScript、Ant Design、API SDK、类型检查、构建验证和 B 端界面规则 |
| `/apps/web/AGENTS.md` | Next.js、Server/Client Components、standalone、Tailwind、shadcn/ui、SEO 和浏览器验收规则 |

根 `AGENTS.md` 必须包含作用域路由说明：修改 `apps/backend/**`、`apps/admin/**` 或 `apps/web/**` 前，确保对应子目录 `AGENTS.md` 已加载；如果已经处于活动指令中，不重复读取。

## Antigravity 桥接规则

`.agents/rules/` 中的文件只包含对应 `AGENTS.md` 的引用，不复制规则正文。

| Rule 文件 | 激活方式 | 引用目标 |
| --- | --- | --- |
| `00-repository.md` | Always On | `@../../AGENTS.md` |
| `10-backend.md` | Glob：`apps/backend/**` | `@../../apps/backend/AGENTS.md` |
| `20-admin.md` | Glob：`apps/admin/**` | `@../../apps/admin/AGENTS.md` |
| `30-web.md` | Glob：`apps/web/**` | `@../../apps/web/AGENTS.md` |

桥接文件由 Antigravity 的 Workspace Rules 机制加载。`00-repository.md` 不含 frontmatter，Antigravity 对无 frontmatter 的规则文件默认视为 Always On，无需显式声明 `trigger: always_on`。三个应用桥接文件均使用 `trigger: glob` 显式声明激活范围。每个 Rule 文件保持精简，并遵守 Antigravity 当前每个 Rule 最多 12,000 字符的限制。

## 全局个人规则边界

全局文件只保存跨项目稳定的个人偏好：

```text
Codex：       ~/.codex/AGENTS.md
Antigravity：~/.gemini/GEMINI.md
```

禁止在全局文件中保存本项目的技术栈、目录、命令、架构决策和业务约束。项目级事实必须保存在仓库中。

## 明确不采用

- 不在项目根目录创建 `GEMINI.md`，避免形成第二份项目规则正文。
- 不创建 `.agents/AGENTS.md`，Antigravity 项目规则统一放在 `.agents/rules/`。
- 不在 `.agents/rules/` 中复制完整规则，避免双份维护。
- 不以 `~/.gemini/GEMINI.md` 中的主动扫描提示替代项目桥接规则，避免换机器或共享仓库后失效。
- 不将长期项目规则写入 `AGENTS.override.md`；该文件只适合临时覆盖。
- 不提前创建空的 `.agents/skills/` 或占位 `SKILL.md`，有真实可复用流程时再增加。

## 指令优先级

发生冲突时按照以下顺序处理：

1. 平台安全规则和用户当前明确要求。
2. 距离目标文件最近的子目录 `AGENTS.md`。
3. 仓库根目录 `AGENTS.md`。
4. 个人全局规则。

下层规则可以细化上层规则，但不得降低安全要求、删除既有功能或扩大用户未授权的操作范围。

## 代价与风险

- 仓库需要额外维护四个很小的 Antigravity 桥接文件。
- Codex 从 Monorepo 根目录启动时，子目录规则可能不在初始指令链中，因此根规则必须包含作用域路由说明。
- Antigravity 的激活方式需要在创建 Rule 时正确设置；错误的 Glob 会导致规则未加载或加载范围过大。
- 工具规则机制未来可能变化，升级工具后需要依据官方文档复核本 ADR。

## 验证要求

规则文件实施后必须分别验证：

1. 在 ChatGPT 桌面客户端的 Codex 视图中，以仓库根目录作为主项目目录创建新任务，确认根 `AGENTS.md` 生效。
2. 分别处理 Backend、Admin 和 Web 路径，确认对应子目录规则已加载。
3. 在 Antigravity 中确认 `00-repository.md` 为 Always On，三个应用规则按各自 Glob 激活。
4. 修改一条测试规则后确认正文只需在对应 `AGENTS.md` 中维护，桥接文件无需同步正文。
5. 确认 Codex 合并后的项目指令未超过 `project_doc_max_bytes`，并确认每个 Antigravity Rule 未超过 12,000 字符。

## 2026-08-29 指令容量门禁补充

Codex 默认 `project_doc_max_bytes` 为 32 KiB。仓库治理门禁按 UTF-8 字节数检查根 `AGENTS.md` 与每个应用级 `AGENTS.md` 的组合，组合上限采用 32 KiB，并至少保留 1 KiB 余量。超限时优先把具体机制迁移到对应专题文档，通过规则入口保留可执行约束和链接，不依赖修改个人 Codex 配置绕过容量问题。

门禁同时确认四个 `.agents/rules/` 桥接文件及其目标存在、引用准确，并拒绝仓库级 `AGENTS.override.md`、`.agents/AGENTS.md` 或其他第二份项目规则正文。

## 官方依据

- [OpenAI Docs：Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [ChatGPT desktop app](https://learn.chatgpt.com/docs/app)
- [Google Antigravity Docs：Rules](https://antigravity.google/docs/rules-workflows)
- [Google Antigravity Docs：Skills](https://antigravity.google/docs/skills)
