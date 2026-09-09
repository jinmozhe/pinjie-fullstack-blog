from app.db.models import Admin, Role

from .permissions import PERMISSION_CODES
from .schemas import AdminRead, RoleRead, RoleSummary


def effective_permissions(admin: Admin) -> list[str]:
    if admin.is_superuser:
        return sorted(PERMISSION_CODES)
    return sorted(
        {
            permission.code
            for role in admin.roles
            if role.is_active
            for permission in role.permissions
            if permission.is_active and permission.code in PERMISSION_CODES
        }
    )


def admin_read(admin: Admin) -> AdminRead:
    return AdminRead(
        id=admin.id,
        username=admin.username,
        display_name=admin.display_name,
        avatar=admin.avatar,
        is_active=admin.is_active,
        is_superuser=admin.is_superuser,
        roles=[RoleSummary.model_validate(role) for role in sorted(admin.roles, key=lambda value: value.code)],
        permissions=effective_permissions(admin),
        created_at=admin.created_at,
        updated_at=admin.updated_at,
    )


def role_read(role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_active=role.is_active,
        permissions=sorted(permission.code for permission in role.permissions if permission.is_active),
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


__all__ = ["admin_read", "effective_permissions", "role_read"]
