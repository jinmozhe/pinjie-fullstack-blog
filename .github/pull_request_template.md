# Pull Request 检查清单

## 变更目标

<!-- 说明用户结果、工程目标和关联计划，不复制完整计划正文。 -->

- 关联计划：
- 关联需求：
- 影响范围：Backend / Admin / Web / API Client / Database / Deployment / Documentation

## 风险与边界

- [ ] 未修改任务范围外的用户资产。
- [ ] 已说明公开 API、权限、数据、迁移、配置和部署影响。
- [ ] 高风险变更已获得相应 Code Owner 评审。
- [ ] 临时兼容已登记负责人、删除日期、观测、回滚和删除测试，或本项不适用。
- [ ] 没有吞错、假成功、弱默认值、静默降级和 `latest` 回退。

## 契约与数据

- [ ] OpenAPI 与 API Client 已按生成顺序同步，或本项不适用。
- [ ] Breaking Change 已完成消费者迁移或受控迁移计划，或本项不适用。
- [ ] Model 变化具有 Alembic 迁移和真实 PostgreSQL 验证，或本项不适用。
- [ ] 不可逆迁移具有已验证备份、恢复和数据校验方案，或本项不适用。

## 安全与隐私

- [ ] 认证、授权和资源权限在服务端生效，或本项不适用。
- [ ] 日志、错误、测试和样本不包含凭据、完整 Token、密码和敏感个人数据。
- [ ] 秘密、依赖、代码和容器安全检查已执行到当前适用阶段。
- [ ] 新增第三方 GitHub Action 已固定完整 Commit SHA，或本项不适用。

## 验证

<!-- 填写实际命令和结果，明确 skipped、未执行和兜底验证。默认轻量门禁之外的 build、Vitest、pytest 和完整验证只有在用户明确授权后才执行。 -->

| 检查 | 结果 | 证据或原因 |
| --- | --- | --- |
| 工作区与模块边界 | | |
| Backend | | |
| Admin | | |
| Web | | |
| OpenAPI / API Client | | |
| Database / Migration | | |
| Security | | |
| Build / Container | | |
| Browser / E2E | | |

## 发布与回滚

- [ ] 本 PR 不自动授权提交、推送、Tag、Release、镜像发布或部署。
- [ ] 回滚目标、数据库兼容范围和观察条件已说明，或本项不适用。
- [ ] 生产候选版本使用完整 Commit SHA 和镜像 digest，或本项不适用。

## 文档同步

- [ ] 计划、PRD、ADR、架构、运维、索引和 Changelog 已按职责同步。
- [ ] 未把临时过程写入长期规则，未复制同一事实形成多份来源。
