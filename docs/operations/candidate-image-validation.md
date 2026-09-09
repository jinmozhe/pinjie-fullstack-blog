# 候选镜像验收工具状态

> 博客适用状态：本文件保留继承工具的操作参考。博客尚未发布、未部署，文内历史验证、资源地址及“当前生产”描述不代表博客实际环境；发布与部署入口已阻断。启用前按[博客发布边界](release-and-rollback.md)配置并评审独立资源。

## 当前状态

当前项目采用单维护者、1Panel 人工部署流程，不使用 `Validate Candidate Images`。发布不需要创建 `candidate-image-validation` Environment、配置 `TCR_READ_USERNAME` / `TCR_READ_PASSWORD`、生成请求 JSON、取得 `deployment-composition.json` / `images.env` 或执行自动变量预检。

实际操作统一以[GitHub 到 1Panel 端到端人工发布手册](github-cnb-tcr-1panel-release-runbook.md)为准。选择源码交接模式、CNB 构建扫描、TCR 人工核验、固定 digest、回滚保护和上线检查继续有效，停止使用候选验收不改变 `strict` / `fast` 的证据要求。

## 实现边界

[候选验收工作流](../../.github/workflows/validate-candidate-images.yml)和[发布工具入口](../../scripts/release/release-tools.mjs)仍保留在仓库，工作流配置仍支持人工触发。本次只更新文档，没有删除实现、修改 GitHub 工作流启用状态或配置远端凭据。当前发布操作不调用这些入口，也不把它们作为待完成事项。

该工具原本用于拉取三端最终 digest、运行隔离 E2E，并生成部署组合供变量预检使用。取消此操作后，Full Validation 仍只证明其源码和构建产物验证范围；人工核验与上线检查不能表述为最终 TCR 镜像组合已通过自动 E2E。

## 镜像保留边界

生产、回滚和待部署的 digest，以及关联扫描、SBOM、provenance 和 OCI 引用仍需保护。按实际运行版本与发布记录人工核对，不因没有候选验收清单而删除镜像或伪造证据。

现存 `retention` 工具依赖有效的部署组合清单，只生成审查建议。当前人工流程不要求使用它，也不要求为了运行它补做候选验收；实际删除仍需独立授权并核对实时库存和引用关系。

决策依据见 [ADR 0008](../adr/0008-不可变发布与生产追溯决策.md)，部署和回滚步骤见[发布与回滚手册](release-and-rollback.md)。
