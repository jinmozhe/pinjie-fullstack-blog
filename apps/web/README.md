# apps/web

个人博客公开阅读网站，基于 Next.js App Router，面向匿名读者。

## 技术栈

- Next.js（App Router，`output: standalone`）
- React 19 + TypeScript + Tailwind CSS 3，PostCSS 与 Autoprefixer
- shadcn 风格的本地基础组件、Radix Dialog/Slot、CSS 设计变量；components.json 登记组件入口
- lucide-react
- TanStack Query v5 与 Zustand 保留给有需要的客户端交互，公开文章默认由 Server Components 读取
- @pinjie/api-client（自动生成 SDK）

## 本地启动

```powershell
pnpm install --frozen-lockfile
pnpm --filter @pinjie/web dev   # http://localhost:3000
```

公开页面通过生成 SDK 在服务端读取 `BACKEND_INTERNAL_URL`；现有浏览器请求代理仍使用同域 `/api/v1`。必须配置有效的 `BACKEND_INTERNAL_URL` 与 `WEB_PUBLIC_ORIGIN`，模板见 `.env.example`；配置或站点读取失败显示明确错误，不返回示例站点数据。

## 生产部署模式

使用 `output: standalone` 容器模式。容器部署默认不依赖进程内 ISR 缓存；公开文章按请求读取，缓存边界遵守 [博客需求](../../docs/PROJECT_REQUIREMENTS.md)。

## 当前范围

已实现首页 `/`、文章 `/posts/{slug}`、分类 `/categories/{slug}`、标签 `/tags/{slug}` 和标题摘要搜索 `/search?q=...`，分页保存在 URL。公开数据仅包含 public 且未删除的文章。`/login`、`/register` 和 `/account` 返回 404，后台管理员登录不受影响。

首页、分类、标签、文章分别生成标题、描述和 canonical；文章提供 BlogPosting JSON-LD，搜索 noindex。`/sitemap.xml` 输出索引，分片按每页 100 项读取公开内容。元信息在流式输出前完成可见性检查，阅读链接使用完整文档导航；HTTP 页面和公开 API 不缓存文章，不承诺撤回用户已下载的历史副本。实现机制见 [博客内容架构](../../docs/architecture/blog-content.md)。

## 设计与实现入口

涉及 UI 的设计、实现、修改和评审必须读取整套 [Web 统一设计标准](../../docs/architecture/web-design-standard.md)，按影响落实统一配色、字体、间距、组件、响应式布局、正文排版及可访问性规则。架构、安全与验证授权继续遵守 [Web 项目规则](AGENTS.md)。

公开页面已接入设计标准；现成组件通过项目源码复用，页面布局使用 Tailwind，正文复杂选择器集中在 globals.css。shadcn 组件采用手工适配的 Radix 方案，保留 MIT 许可；新增组件需要核对当前 Tailwind 3 与变量格式，禁止直接覆盖主题。效果图中的文章和图片不作为真实数据。

## 质量检查

默认自动检查：

```powershell
pnpm --filter @pinjie/web lint
pnpm --filter @pinjie/web typecheck
```

以下专项命令仅供用户自行执行，或在当前任务明确点名授权后执行；普通开发、提交、推送不包含这些验证：

```powershell
pnpm --filter @pinjie/web test
pnpm --filter @pinjie/web build
```

Playwright、axe 和其他浏览器自动化也需单独明确授权。纯文档修改按根规则运行适用文档与治理检查；未执行的专项验证不能记为通过。
