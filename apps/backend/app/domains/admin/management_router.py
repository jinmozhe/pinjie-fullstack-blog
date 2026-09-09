import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    AdminManagementServiceDependency,
    require_admin_csrf,
    require_permission,
    require_superuser,
)
from app.core.context import current_request_id
from app.core.privacy import masked_ip
from app.core.response import ResponseModel, success_response
from app.db.models import AdminSession, UserSession
from app.domains.auth.schemas import UserPrincipalOut
from app.domains.users.schemas import ActionResult, SessionPage, SessionRead, UserUpdateIn

from .permissions import PermissionCode
from .presenters import admin_read, role_read
from .schemas import (
    AdminBulkStatusUpdateIn,
    AdminCreateIn,
    AdminPage,
    AdminRead,
    AdminRoleAssignIn,
    AdminSuperuserUpdateIn,
    AdminUpdateIn,
    AdminUserCreateIn,
    AdminUserRead,
    AuditEventPage,
    BatchActionResult,
    LoginEventPage,
    PasswordResetIn,
    PermissionRead,
    RequestLogPage,
    RoleBulkDeleteIn,
    RoleBulkStatusUpdateIn,
    RoleCreateIn,
    RolePage,
    RolePermissionAssignIn,
    RoleRead,
    RoleUpdateIn,
    StatusUpdateIn,
    SystemOverviewRead,
    UserBulkDeleteIn,
    UserBulkStatusUpdateIn,
    UserPage,
    UserRestoreBatchIn,
)

router = APIRouter(prefix="/admin", tags=["后台管理"])


def _session_read(item: UserSession | AdminSession) -> SessionRead:
    return SessionRead(
        id=item.id,
        device_name=item.device_name,
        ip_masked=masked_ip(item.ip_address),
        user_agent_summary=item.user_agent_summary,
        created_at=item.created_at,
        last_seen_at=item.last_seen_at,
        idle_expires_at=item.idle_expires_at,
        absolute_expires_at=item.absolute_expires_at,
        is_current=False,
        revoked_at=item.revoked_at,
    )


@router.get(
    "/users",
    response_model=ResponseModel[UserPage],
    dependencies=[Depends(require_permission(PermissionCode.USERS_READ))],
    summary="获取用户列表",
)
async def list_users(
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    lifecycle: Annotated[Literal["all", "active", "inactive", "deleted"], Query()] = "all",
) -> ResponseModel[UserPage]:
    result = await service.list_users(page=page, page_size=page_size, search=search, lifecycle=lifecycle)
    return success_response(data=result, request_id=current_request_id())


@router.post(
    "/users",
    response_model=ResponseModel[AdminUserRead],
    status_code=201,
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.USERS_CREATE))],
    summary="创建用户",
    description="由具备独立权限的管理员创建普通用户账户，不受公开注册开关影响且不创建登录会话。",
)
async def create_user(
    payload: AdminUserCreateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[AdminUserRead]:
    return success_response(
        data=await service.create_user(payload),
        request_id=current_request_id(),
        message="用户创建成功",
    )


@router.patch(
    "/users/status/batch",
    response_model=ResponseModel[BatchActionResult],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.USERS_UPDATE))],
    summary="批量修改用户状态",
)
async def set_user_status_bulk(
    payload: UserBulkStatusUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[BatchActionResult]:
    return success_response(
        data=await service.set_user_status_bulk(payload),
        request_id=current_request_id(),
        message="用户状态批量更新成功",
    )


@router.delete(
    "/users/batch",
    response_model=ResponseModel[BatchActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.USERS_DELETE)),
    ],
    summary="批量软删除用户",
    description="将明确选中的用户账户移入回收站并停用，记录可选删除原因并撤销其全部会话。",
)
async def delete_users_bulk(
    payload: UserBulkDeleteIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[BatchActionResult]:
    return success_response(
        data=await service.delete_users_bulk(payload),
        request_id=current_request_id(),
        message="用户批量删除成功",
    )


@router.post(
    "/users/restore/batch",
    response_model=ResponseModel[BatchActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.USERS_RESTORE)),
    ],
    summary="批量恢复回收站用户",
    description="恢复回收站中的用户，恢复后账户保持停用。",
)
async def restore_users_bulk(
    payload: UserRestoreBatchIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[BatchActionResult]:
    return success_response(
        data=await service.restore_users_bulk(payload),
        request_id=current_request_id(),
        message="用户批量恢复成功",
    )


@router.post(
    "/users/{user_id}/restore",
    response_model=ResponseModel[AdminUserRead],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.USERS_RESTORE)),
    ],
    summary="恢复回收站用户",
    description="恢复回收站中的用户，恢复后账户保持停用。",
)
async def restore_user(
    user_id: uuid.UUID,
    service: AdminManagementServiceDependency,
) -> ResponseModel[AdminUserRead]:
    return success_response(
        data=await service.restore_user(user_id),
        request_id=current_request_id(),
        message="用户恢复成功",
    )


@router.get(
    "/users/{user_id}",
    response_model=ResponseModel[UserPrincipalOut],
    dependencies=[Depends(require_permission(PermissionCode.USERS_READ))],
    summary="获取用户详情",
)
async def get_user(user_id: uuid.UUID, service: AdminManagementServiceDependency) -> ResponseModel[UserPrincipalOut]:
    return success_response(
        data=UserPrincipalOut.model_validate(await service.get_user(user_id)), request_id=current_request_id()
    )


@router.patch(
    "/users/{user_id}",
    response_model=ResponseModel[UserPrincipalOut],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.USERS_UPDATE))],
    summary="更新用户资料",
)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[UserPrincipalOut]:
    user = await service.update_user(user_id, payload)
    return success_response(
        data=UserPrincipalOut.model_validate(user), request_id=current_request_id(), message="用户更新成功"
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=ResponseModel[UserPrincipalOut],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.USERS_UPDATE))],
    summary="修改用户状态",
)
async def set_user_status(
    user_id: uuid.UUID,
    payload: StatusUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[UserPrincipalOut]:
    user = await service.set_user_status(user_id, payload)
    return success_response(
        data=UserPrincipalOut.model_validate(user), request_id=current_request_id(), message="用户状态更新成功"
    )


@router.put(
    "/users/{user_id}/credentials/password",
    response_model=ResponseModel[ActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.USERS_CREDENTIALS_RESET)),
    ],
    summary="重置用户密码",
)
async def reset_user_password(
    user_id: uuid.UUID,
    payload: PasswordResetIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[ActionResult]:
    await service.reset_user_password(user_id, payload)
    return success_response(data=ActionResult(), request_id=current_request_id(), message="密码重置成功")


@router.get(
    "/users/{user_id}/sessions",
    response_model=ResponseModel[SessionPage],
    dependencies=[Depends(require_permission(PermissionCode.USERS_SESSIONS_READ))],
    summary="获取用户会话列表",
)
async def list_user_sessions(
    user_id: uuid.UUID,
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[SessionPage]:
    items, total = await service.list_user_sessions(user_id, page=page, page_size=page_size)
    return success_response(
        data=SessionPage.create(
            items=[_session_read(item) for item in items], page=page, page_size=page_size, total=total
        ),
        request_id=current_request_id(),
    )


@router.delete(
    "/users/{user_id}/sessions/{session_id}",
    response_model=ResponseModel[ActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.USERS_SESSIONS_REVOKE)),
    ],
    summary="撤销用户指定会话",
)
async def revoke_user_session(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    service: AdminManagementServiceDependency,
) -> ResponseModel[ActionResult]:
    await service.revoke_user_session(user_id, session_id)
    return success_response(data=ActionResult(), request_id=current_request_id(), message="会话撤销成功")


@router.post(
    "/users/{user_id}/sessions/revoke-all",
    response_model=ResponseModel[ActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.USERS_SESSIONS_REVOKE)),
    ],
    summary="撤销用户全部会话",
)
async def revoke_all_user_sessions(
    user_id: uuid.UUID, service: AdminManagementServiceDependency
) -> ResponseModel[ActionResult]:
    await service.revoke_all_user_sessions(user_id)
    return success_response(data=ActionResult(), request_id=current_request_id(), message="全部会话撤销成功")


@router.get(
    "/admins",
    response_model=ResponseModel[AdminPage],
    dependencies=[Depends(require_permission(PermissionCode.ADMINS_READ))],
    summary="获取管理员列表",
)
async def list_admins(
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[AdminPage]:
    return success_response(
        data=await service.list_admins(page=page, page_size=page_size), request_id=current_request_id()
    )


@router.patch(
    "/admins/status/batch",
    response_model=ResponseModel[list[AdminRead]],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ADMINS_UPDATE)),
    ],
    summary="批量修改管理员状态",
)
async def set_admin_status_bulk(
    payload: AdminBulkStatusUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[list[AdminRead]]:
    admins = await service.set_admin_status_bulk(payload)
    return success_response(
        data=[admin_read(admin) for admin in admins],
        request_id=current_request_id(),
        message="管理员状态批量更新成功",
    )


@router.post(
    "/admins",
    response_model=ResponseModel[AdminRead],
    status_code=201,
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ADMINS_CREATE)),
    ],
    summary="创建管理员",
)
async def create_admin(payload: AdminCreateIn, service: AdminManagementServiceDependency) -> ResponseModel[AdminRead]:
    return success_response(
        data=admin_read(await service.create_admin(payload)),
        request_id=current_request_id(),
        message="管理员创建成功",
    )


@router.get(
    "/admins/{admin_id}",
    response_model=ResponseModel[AdminRead],
    dependencies=[Depends(require_permission(PermissionCode.ADMINS_READ))],
    summary="获取管理员详情",
)
async def get_admin(admin_id: uuid.UUID, service: AdminManagementServiceDependency) -> ResponseModel[AdminRead]:
    return success_response(data=admin_read(await service.get_admin(admin_id)), request_id=current_request_id())


@router.patch(
    "/admins/{admin_id}",
    response_model=ResponseModel[AdminRead],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.ADMINS_UPDATE))],
    summary="更新管理员资料",
)
async def update_admin(
    admin_id: uuid.UUID,
    payload: AdminUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[AdminRead]:
    return success_response(
        data=admin_read(await service.update_admin(admin_id, payload)),
        request_id=current_request_id(),
        message="管理员更新成功",
    )


@router.patch(
    "/admins/{admin_id}/superuser",
    response_model=ResponseModel[AdminRead],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ADMINS_SUPERUSER_CHANGE)),
        Depends(require_superuser),
    ],
    summary="修改管理员超级管理员身份",
    description="仅当前超级管理员可以授予或取消其他管理员的超级管理员身份。",
)
async def set_admin_superuser(
    admin_id: uuid.UUID,
    payload: AdminSuperuserUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[AdminRead]:
    return success_response(
        data=admin_read(await service.set_admin_superuser(admin_id, payload)),
        request_id=current_request_id(),
        message="管理员身份更新成功",
    )


@router.patch(
    "/admins/{admin_id}/status",
    response_model=ResponseModel[AdminRead],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.ADMINS_UPDATE))],
    summary="修改管理员状态",
)
async def set_admin_status(
    admin_id: uuid.UUID,
    payload: StatusUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[AdminRead]:
    return success_response(
        data=admin_read(await service.set_admin_status(admin_id, payload)),
        request_id=current_request_id(),
        message="管理员状态更新成功",
    )


@router.put(
    "/admins/{admin_id}/credentials/password",
    response_model=ResponseModel[ActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ADMINS_CREDENTIALS_RESET)),
    ],
    summary="重置管理员密码",
)
async def reset_admin_password(
    admin_id: uuid.UUID,
    payload: PasswordResetIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[ActionResult]:
    await service.reset_admin_password(admin_id, payload)
    return success_response(data=ActionResult(), request_id=current_request_id(), message="密码重置成功")


@router.put(
    "/admins/{admin_id}/roles",
    response_model=ResponseModel[AdminRead],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ADMINS_ROLES_ASSIGN)),
    ],
    summary="分配管理员角色",
)
async def assign_admin_roles(
    admin_id: uuid.UUID,
    payload: AdminRoleAssignIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[AdminRead]:
    return success_response(
        data=admin_read(await service.assign_admin_roles(admin_id, payload)),
        request_id=current_request_id(),
        message="角色分配成功",
    )


@router.get(
    "/admins/{admin_id}/sessions",
    response_model=ResponseModel[SessionPage],
    dependencies=[Depends(require_permission(PermissionCode.ADMINS_SESSIONS_READ))],
    summary="获取管理员会话列表",
)
async def list_admin_sessions(
    admin_id: uuid.UUID,
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[SessionPage]:
    items, total = await service.list_admin_sessions(admin_id, page=page, page_size=page_size)
    return success_response(
        data=SessionPage.create(
            items=[_session_read(item) for item in items], page=page, page_size=page_size, total=total
        ),
        request_id=current_request_id(),
    )


@router.post(
    "/admins/{admin_id}/sessions/revoke-all",
    response_model=ResponseModel[ActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ADMINS_SESSIONS_REVOKE)),
    ],
    summary="撤销管理员全部会话",
)
async def revoke_all_admin_sessions(
    admin_id: uuid.UUID, service: AdminManagementServiceDependency
) -> ResponseModel[ActionResult]:
    await service.revoke_all_admin_sessions(admin_id)
    return success_response(data=ActionResult(), request_id=current_request_id(), message="全部会话撤销成功")


@router.get(
    "/roles",
    response_model=ResponseModel[RolePage],
    dependencies=[Depends(require_permission(PermissionCode.ROLES_READ))],
    summary="获取角色列表",
)
async def list_roles(
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[RolePage]:
    return success_response(
        data=await service.list_roles(page=page, page_size=page_size), request_id=current_request_id()
    )


@router.patch(
    "/roles/status/batch",
    response_model=ResponseModel[BatchActionResult],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.ROLES_UPDATE))],
    summary="批量修改角色状态",
)
async def set_role_status_bulk(
    payload: RoleBulkStatusUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[BatchActionResult]:
    return success_response(
        data=await service.set_role_status_bulk(payload),
        request_id=current_request_id(),
        message="角色状态批量更新成功",
    )


@router.delete(
    "/roles/batch",
    response_model=ResponseModel[BatchActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ROLES_DELETE)),
    ],
    summary="批量删除未使用角色",
)
async def delete_roles_bulk(
    payload: RoleBulkDeleteIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[BatchActionResult]:
    return success_response(
        data=await service.delete_roles_bulk(payload),
        request_id=current_request_id(),
        message="角色批量删除成功",
    )


@router.post(
    "/roles",
    response_model=ResponseModel[RoleRead],
    status_code=201,
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.ROLES_CREATE))],
    summary="创建角色",
)
async def create_role(payload: RoleCreateIn, service: AdminManagementServiceDependency) -> ResponseModel[RoleRead]:
    return success_response(
        data=role_read(await service.create_role(payload)), request_id=current_request_id(), message="角色创建成功"
    )


@router.get(
    "/roles/{role_id}",
    response_model=ResponseModel[RoleRead],
    dependencies=[Depends(require_permission(PermissionCode.ROLES_READ))],
    summary="获取角色详情",
)
async def get_role(role_id: uuid.UUID, service: AdminManagementServiceDependency) -> ResponseModel[RoleRead]:
    return success_response(data=role_read(await service.get_role(role_id)), request_id=current_request_id())


@router.patch(
    "/roles/{role_id}",
    response_model=ResponseModel[RoleRead],
    dependencies=[Depends(require_admin_csrf), Depends(require_permission(PermissionCode.ROLES_UPDATE))],
    summary="更新角色",
)
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdateIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[RoleRead]:
    return success_response(
        data=role_read(await service.update_role(role_id, payload)),
        request_id=current_request_id(),
        message="角色更新成功",
    )


@router.delete(
    "/roles/{role_id}",
    response_model=ResponseModel[ActionResult],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ROLES_DELETE)),
    ],
    summary="删除未使用的角色",
)
async def delete_role(role_id: uuid.UUID, service: AdminManagementServiceDependency) -> ResponseModel[ActionResult]:
    await service.delete_role(role_id)
    return success_response(data=ActionResult(), request_id=current_request_id(), message="角色删除成功")


@router.put(
    "/roles/{role_id}/permissions",
    response_model=ResponseModel[RoleRead],
    dependencies=[
        Depends(require_admin_csrf),
        Depends(require_permission(PermissionCode.ROLES_PERMISSIONS_ASSIGN)),
    ],
    summary="分配角色权限",
)
async def assign_role_permissions(
    role_id: uuid.UUID,
    payload: RolePermissionAssignIn,
    service: AdminManagementServiceDependency,
) -> ResponseModel[RoleRead]:
    return success_response(
        data=role_read(await service.assign_role_permissions(role_id, payload)),
        request_id=current_request_id(),
        message="权限分配成功",
    )


@router.get(
    "/permissions",
    response_model=ResponseModel[list[PermissionRead]],
    dependencies=[Depends(require_permission(PermissionCode.PERMISSIONS_READ))],
    summary="获取源码管理的权限目录",
)
async def list_permissions(
    service: AdminManagementServiceDependency,
) -> ResponseModel[list[PermissionRead]]:
    return success_response(data=await service.list_permissions(), request_id=current_request_id())


@router.get(
    "/security/login-events",
    response_model=ResponseModel[LoginEventPage],
    dependencies=[Depends(require_permission(PermissionCode.SECURITY_LOGIN_EVENTS_READ))],
    summary="获取身份认证安全事件",
)
async def list_login_events(
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[LoginEventPage]:
    return success_response(
        data=await service.list_login_events(page=page, page_size=page_size), request_id=current_request_id()
    )


@router.get(
    "/security/audit-events",
    response_model=ResponseModel[AuditEventPage],
    dependencies=[Depends(require_permission(PermissionCode.SECURITY_AUDIT_EVENTS_READ))],
    summary="获取管理员审计事件",
)
async def list_audit_events(
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[AuditEventPage]:
    return success_response(
        data=await service.list_audit_events(page=page, page_size=page_size), request_id=current_request_id()
    )


@router.get(
    "/system/request-logs",
    response_model=ResponseModel[RequestLogPage],
    dependencies=[Depends(require_permission(PermissionCode.SYSTEM_REQUEST_LOGS_READ))],
    summary="获取可选请求元数据日志",
)
async def list_request_logs(
    service: AdminManagementServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResponseModel[RequestLogPage]:
    return success_response(
        data=await service.list_request_logs(page=page, page_size=page_size), request_id=current_request_id()
    )


@router.get(
    "/system/overview",
    response_model=ResponseModel[SystemOverviewRead],
    dependencies=[Depends(require_permission(PermissionCode.SYSTEM_OVERVIEW_READ))],
    summary="获取系统全景监控概览",
    description="聚合实时基础设施探针、公开运行环境摘要以及带 Redis 缓存和采样时间的业务资产统计。",
)
async def get_system_overview(
    service: AdminManagementServiceDependency,
) -> ResponseModel[SystemOverviewRead]:
    return success_response(
        data=await service.get_system_overview(),
        request_id=current_request_id(),
    )


__all__ = ["router"]
