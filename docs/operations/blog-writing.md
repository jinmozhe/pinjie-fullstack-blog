# 博客后台启用与写作

## 当前范围

后台提供文章、分类标签、Markdown 预览、图片与回收站管理。公开文章接口和访客阅读页面已接入：配置并启动 Backend/Web 后，公开且未删除文章可从首页与 `/posts/{slug}` 访问，分类标签与标题摘要搜索同步读取公开内容。代码已接入不代表数据库迁移、真实写作或浏览器验收已经执行，启用前仍须完成下文环境步骤。

以下步骤由操作人员在本机执行，命令逐条运行并核对结果。已有本地环境不需要重新创建数据库、管理员或覆盖 `.env`。项目路径为 `E:\fastapi\pinjie-fullstack-blog`。

## 一次性启用

1. 先停止自己正在运行的 Backend 开发终端，核对 `apps/backend/.env` 的目标是博客开发库 `pinjie_blog_dev`。有需要保留的数据时，先按 [数据库备份恢复手册](database-backup-restore.md) 备份数据库与图片。不要将密码、密钥粘贴到终端命令、聊天或 Git。
2. 同步锁定依赖：

   ```powershell
   Set-Location E:\fastapi\pinjie-fullstack-blog
   pnpm install --frozen-lockfile
   Set-Location apps\backend
   uv sync --locked
   ```

3. 核对当前迁移，确认目标库后执行升级，再核对版本：

   ```powershell
   uv run alembic current
   uv run alembic upgrade head
   uv run alembic current
   ```

   当前新增迁移为 `20260909_01`，增加文章、分类、标签及两张关联表。`alembic upgrade` 使用 `.env` 数据库，命令本身不会要求输入确认库名。任何失败先排障，不执行 downgrade、删表或重建库。

4. 查看权限目录差异：

   ```powershell
   uv run python -m scripts.sync_permissions --check --confirm-database pinjie_blog_dev
   ```

   新增文章 5 项、分类 4 项、标签 4 项权限；目录版本更新也可能使原权限计入 changed。检测到差异时脚本退出码为 1，这是差异提示。若有数据库连接或执行异常，先修复异常。

5. 确认同步到上述博客库后执行：

   ```powershell
   uv run python -m scripts.sync_permissions --apply --confirm-database pinjie_blog_dev
   uv run python -m scripts.sync_permissions --check --confirm-database pinjie_blog_dev
   ```

   最后应无目录差异。沿用已有超级管理员，不重复创建或重置密码；普通管理员需要由已有权限管理功能显式分配所需内容权限。重新登录后台以刷新菜单与权限信息。

## 日常启动

PostgreSQL 与项目 Redis 应已启动。三个独立 VS Code PowerShell 终端分别执行：

```powershell
# 终端一：Backend
Set-Location E:\fastapi\pinjie-fullstack-blog\apps\backend
uv run uvicorn app.main:app --reload --host localhost --port 8000
```

```powershell
# 终端二：Admin
Set-Location E:\fastapi\pinjie-fullstack-blog
pnpm --filter @pinjie/admin dev
```

```powershell
# 终端三：Web，需要查看现有网站时启动
Set-Location E:\fastapi\pinjie-fullstack-blog
pnpm --filter @pinjie/web dev
```

访问 [后台文章管理](http://localhost:3001/blog/posts)、[Backend 接口文档](http://localhost:8000/docs) 和 [Web](http://localhost:3000)。日常启动不必重复迁移或权限同步。

如果沿用旧本地配置，手工对照三端 `.env.example` 更新 Backend 的 `WEB_ORIGINS`、`ADMIN_ORIGINS`，以及 Admin/Web 的 `BACKEND_INTERNAL_URL` 和 Web 的 `WEB_PUBLIC_ORIGIN`；分别使用 localhost 的 3000、3001、8000。保留自己现有的数据库和密钥。不要混用 localhost 与 127.0.0.1，修改配置后重启对应服务。生产端口策略见 [本地开发手册](local-dev-environment.md)。

## 写作操作

1. 按需创建分类、标签，也可以都不选。
2. 进入“写文章”，填写标题、固定网址标识和 Markdown，可选摘要与封面。工具栏支持插入图片和代码块，预览由 Backend 渲染。
3. 点击“发布”后文章才保存；关闭或离开未保存页面会提示。发布失败保留输入，没有自动草稿恢复功能。
4. 编辑文章点击“保存”立即更新当前内容，保持原公开或隐藏状态。网址标识与首次发布时间保持不变。
5. 列表可切换公开/隐藏，按分类、标签和北京时间日期筛选。删除需确认；回收站支持单条、批量恢复，恢复后隐藏，再单独公开。
6. 删除分类或标签先查看目标与受影响文章数，确认后解除关联并删除。文章保留，其他标签保留，回收站里的关联也同步处理。

图片上传即保存为独立资产。隐藏、删除文章不撤销已知图片直链；在用图片不能从资产列表删除。取消写作后未引用图片可人工清理。图片更换和引用规则见 [博客内容架构](../architecture/blog-content.md)。

## 常见情况

| 情况 | 处理 |
| --- | --- |
| 接口提示数据表不存在或内容服务不可用 | 先核对数据库与迁移版本，不重复发布，不清空数据库 |
| 后台没有内容菜单或提示权限不足 | 核对权限目录同步，重新登录；检查账号实际权限 |
| 保存返回 412 | 保留当前文字，再重新加载文章核对；不要循环提交旧数据 |
| 分类标签删除返回 412 | 取消原确认，重新预览影响再决定 |
| 图片删除返回 409 | 先从包括回收站在内的文章解除引用并保存，再决定是否删除图片 |
| Markdown 图片保存被拒绝 | 通过文章上传按钮插入本站图片，正文不支持外站图片 |

本轮交付只完成源码与轻量检查，未执行数据库迁移、pytest、Vitest、浏览器或构建验收。完成上述启用后，可人工检查“写作、上传、发布、编辑、隐藏、删除、恢复”；正式上线前另行明确专项验证与发布部署范围。
