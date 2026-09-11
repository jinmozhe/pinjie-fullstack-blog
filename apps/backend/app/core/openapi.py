from typing import Any

OPENAPI_TAGS = [
    {"name": "公开博客", "description": "匿名读取公开文章、分类标签、标题摘要搜索与安全正文。"},
    {"name": "博客管理", "description": "文章、分类标签、回收站和安全 Markdown 预览。"},
    {"name": "用户认证", "description": "用户注册、登录、刷新会话和退出登录接口。"},
    {"name": "用户账户", "description": "当前用户资料、密码、登录会话和账户管理接口。"},
    {"name": "管理员认证", "description": "管理员登录、刷新会话、修改密码和敏感操作确认接口。"},
    {"name": "后台管理", "description": "用户、管理员、角色、权限和安全审计管理接口。"},
    {"name": "文件资产", "description": "双域文件上传、管理员资产查询与受控删除接口。"},
    {"name": "系统", "description": "面向应用调用方的公共系统状态接口。"},
    {"name": "系统设置", "description": "受权限保护的站点资料、配置媒体和公开注册设置接口。"},
    {"name": "健康检查", "description": "面向运行平台的存活与就绪探针。"},
]

_RESPONSE_DESCRIPTIONS = {
    "Successful Response": "请求成功",
    "Validation Error": "请求参数校验失败",
}

_FIELD_DESCRIPTIONS = {
    "absolute_expires_at": "会话绝对过期时间",
    "access_expires_at": "访问凭据过期时间",
    "action": "操作代码",
    "actor_id": "操作管理员唯一标识",
    "avatar": "管理员头像 URL 或站内资源路径",
    "catalog_version": "权限目录版本",
    "changed_fields": "本次操作涉及的字段摘要",
    "checks": "各项就绪依赖的安全状态摘要",
    "code": "稳定程序代码",
    "completed": "操作是否已经完成",
    "completed_at": "操作完成时间",
    "confirmation_token": "敏感操作短期确认凭据",
    "created_at": "创建时间",
    "ctx": "参数校验错误的补充上下文",
    "data": "响应业务数据",
    "description": "资源说明文本",
    "detail": "请求参数校验错误详情列表",
    "device_name": "登录设备名称",
    "display_name": "展示名称",
    "duration_ms": "请求处理耗时，单位为毫秒",
    "email": "电子邮箱地址",
    "event_type": "安全事件类型代码",
    "file_hash": "文件内容的 SHA-256 哈希值",
    "file_key": "存储驱动中的相对文件键",
    "file_size": "文件大小，单位为字节",
    "expires_at": "凭据过期时间",
    "id": "资源唯一标识",
    "idle_expires_at": "会话空闲过期时间",
    "input": "引发校验错误的输入值，敏感内容可能被省略",
    "ip_address": "请求来源 IP 地址",
    "ip_masked": "脱敏后的请求来源 IP 地址",
    "is_active": "资源当前是否启用",
    "is_current": "是否为当前登录会话",
    "is_superuser": "管理员是否拥有超级管理员身份",
    "items": "当前分页中的资源列表",
    "last_seen_at": "会话最近活动时间",
    "loc": "错误字段在请求中的位置",
    "message": "面向调用方的中文结果消息",
    "method": "HTTP 请求方法",
    "mime_type": "服务端探测得到的真实 MIME 类型",
    "msg": "参数校验错误消息",
    "name": "资源名称",
    "occurred_at": "事件发生时间",
    "original_name": "上传时经过路径剥离的原始文件名",
    "page": "当前页码，从 1 开始",
    "page_size": "每页资源数量",
    "permission_codes": "分配给角色的权限代码列表",
    "permissions": "当前主体拥有的权限代码列表",
    "principal": "当前认证主体信息",
    "principal_id": "认证主体唯一标识",
    "principal_type": "认证主体类型",
    "reason_code": "事件原因代码",
    "release_version": "处理请求的应用发布版本",
    "request_body": "脱敏并截断后的错误 JSON 请求体",
    "request_id": "用于定位本次请求的唯一标识",
    "result": "操作结果代码",
    "revoked_at": "会话撤销时间",
    "role_ids": "分配给管理员的角色唯一标识列表",
    "roles": "管理员当前拥有的角色列表",
    "route_template": "规范化后的 API 路由模板",
    "scene": "受控的文件使用场景",
    "session_id": "登录会话唯一标识",
    "status": "当前状态代码",
    "status_code": "HTTP 响应状态码",
    "storage_driver": "保存文件的存储驱动代码",
    "succeeded": "安全事件是否成功",
    "target_id": "操作目标唯一标识",
    "target_type": "操作目标类型",
    "total": "符合条件的资源总数",
    "total_pages": "符合条件的总页数",
    "trace_id": "用于关联跨组件调用链的唯一标识",
    "type": "参数校验错误类型",
    "updated_at": "最近更新时间",
    "user_agent_summary": "脱敏后的客户端标识摘要",
    "username": "登录用户名",
    "uploader_id": "上传主体唯一标识",
    "uploader_type": "上传主体类型",
    "url": "文件的公开访问 URL 或站内路径",
}


def _localize_schema_fields(schema: dict[str, Any]) -> None:
    components = schema.get("components", {})
    if not isinstance(components, dict):
        return
    schemas = components.get("schemas", {})
    if not isinstance(schemas, dict):
        return
    for component in schemas.values():
        if not isinstance(component, dict):
            continue
        properties = component.get("properties", {})
        if not isinstance(properties, dict):
            continue
        for field_name, field_schema in properties.items():
            if not isinstance(field_schema, dict) or field_schema.get("description"):
                continue
            description = _FIELD_DESCRIPTIONS.get(field_name)
            if description:
                field_schema["description"] = description


def localize_openapi_schema(schema: dict[str, Any]) -> dict[str, Any]:
    paths = schema.get("paths", {})
    if isinstance(paths, dict):
        for path_item in paths.values():
            if not isinstance(path_item, dict):
                continue
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                responses = operation.get("responses", {})
                if not isinstance(responses, dict):
                    continue
                for response in responses.values():
                    if not isinstance(response, dict):
                        continue
                    description = response.get("description")
                    if isinstance(description, str):
                        response["description"] = _RESPONSE_DESCRIPTIONS.get(description, description)
    _localize_schema_fields(schema)
    return schema


__all__ = ["OPENAPI_TAGS", "localize_openapi_schema"]
