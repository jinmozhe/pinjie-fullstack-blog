# Web 项目规则

## 作用范围与技术栈

- 本文件适用于 `apps/web/**`，并继承仓库根 `AGENTS.md`。
- Web 是匿名博客阅读应用，采用 Next.js App Router、React、TypeScript、Tailwind CSS 3、shadcn 本地组件、Radix UI 和 lucide-react。TanStack Query 与 Zustand 仅用于需要的客户端交互，公开内容默认由 Server Components 读取。
- 新增依赖前先确认仓库现状，遵守依赖准入并更新 workspace 锁文件。

## 目录与渲染边界

- `src/app/` 保持薄路由，只承载路由、布局、Metadata、数据入口和错误边界；领域 UI、Hooks、请求封装和状态进入 `src/features/<domain>/`。
- 跨领域基础组件放 `src/components/`，通用基础设施放 `src/lib/`，客户端状态放 `src/stores/`。Web 与 Admin 禁止直接互相引用。
- Feature 只能通过明确公共入口协作，不得导入其他 Feature 的内部组件、Hook、Store 或请求实现。完整边界见 `docs/architecture/module-boundaries.md`。
- 默认使用 Server Components。仅在需要浏览器 API、事件处理、本地交互状态或客户端数据订阅时添加 `"use client"`，并把客户端边界压到最小。
- 服务端数据和缓存由 Server Components 或 TanStack Query 管理。Zustand 只保存真正的客户端状态，禁止复制服务端数据。
- 临时交互状态优先使用组件本地状态。Zustand 不保存 Token、Cookie 内容和其他敏感凭据；缓存新鲜度按数据语义设置，不用全局固定值代替领域判断。

## API、SSR 与 SEO

- 通过 `@pinjie/api-client` 使用后端契约，页面层消费解包后的业务数据。禁止手工修改生成客户端或重复定义 OpenAPI DTO。
- 服务端请求使用仅服务端可见的后端地址，浏览器请求只使用公开地址。`NEXT_PUBLIC_` 变量会进入客户端产物，严禁保存密钥。
- 浏览器认证优先使用具备 `HttpOnly`、`Secure` 和合适 `SameSite` 属性的 Cookie，并设计 CSRF 防护。Token 禁止进入 `localStorage`、Zustand、URL 和页面源码。
- 需要收录的页面必须提供准确的静态或动态 Metadata、语义化标题、canonical 和必要的结构化数据，并保持 SSR 首屏内容可用。
- Next.js 动态 params 按 Promise 解包；根布局维护标题模板，页面维护自己的 canonical，嵌套 Metadata 按浅合并规则明确继承。公开内容按请求读取并共用可见性过滤；读取与 SEO 机制统一见 [博客内容架构](../../docs/architecture/blog-content.md)。
- `next.config.ts` 保持 `output: "standalone"`，满足生产容器部署。容器部署默认不依赖进程内 ISR 缓存；需要增量缓存时先设计共享缓存和失效策略。

## UI 与可访问性

- 涉及 Web 页面、布局、组件、样式及交互的设计、实现、修改和评审，必须读取并遵守整套 [Web 统一设计标准](../../docs/architecture/web-design-standard.md)，并落实与当前变更相关的条款。颜色、字体、间距、组件、响应式、正文排版和可访问性详细规则仅在该标准维护。

## 验证

- Web 的默认自动门禁只有 `pnpm --filter @pinjie/web typecheck` 和 `pnpm --filter @pinjie/web lint`。日常开发、普通提交、`$git-sync`、Push 和 Pull Request 均遵守这一范围。
- 阶段 B 采用 Vitest、React Testing Library、jsdom 和 MSW 作为单元与组件测试栈，并使用 Playwright 执行真实浏览器跨栈 E2E；关键页面通过 axe 自动扫描可访问性。异步 Server Component 和跨 Server、Client 边界行为由 Playwright 覆盖，详细分层遵守 `docs/architecture/testing-strategy.md`。
- 未经用户在当前任务中明确点名，禁止运行 Web production build、定向或全量 Vitest、Playwright、axe 浏览器扫描及其他浏览器自动化。`$git-sync` 不提供隐式授权，GitHub Actions 的 Push、Pull Request 和定时触发也不得执行这些命令。
- 用户明确授权时只执行被点名的命令和范围，授权不延续到后续任务；测试或构建失败必须如实报告。未获授权的项目记录为“按项目策略未执行”，不能表述为通过或待 GitSync 执行。
- 测试、构建和 E2E 脚本继续保留，供用户本地人工检查或明确授权的专项验证使用。人工页面体验没有可核验证据时，不记为自动测试或完整跨栈通过。
- 应用出现入口但缺少测试脚本或必要测试时属于 `partial`，仓库门禁必须失败，禁止退回空骨架规避检查。
- 用户明确授权浏览器验证时，检查桌面和移动端的首页可见性、关键区块、交互状态和 `document` 横向溢出。
- Windows 下启动开发服务时优先使用稳定的短会话或直接调用 Next CLI。结束验证后核对端口和 PID，只停止本次启动的 Next、Playwright 或浏览器测试进程。
