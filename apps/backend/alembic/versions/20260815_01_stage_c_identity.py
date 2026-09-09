"""Add stage C identity, session, RBAC, and audit tables.

Revision ID: 20260815_01
Revises:
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260815_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[sa.DateTime], sa.Column[sa.DateTime]]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False, comment="规范化用户名"),
        sa.Column("email", sa.String(length=320), nullable=True, comment="未验证可选邮箱"),
        sa.Column("display_name", sa.String(length=100), nullable=True, comment="展示名称"),
        sa.Column("password_hash", sa.String(length=255), nullable=False, comment="Argon2id 密码摘要"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否允许登录"),
        sa.Column("credential_version", sa.Integer(), nullable=False, comment="凭据版本"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="注销时间"),
        *_timestamps(),
        sa.CheckConstraint("credential_version >= 1", name="ck_users_credential_version_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
        comment="C 端用户账户",
    )
    op.create_index("ix_users_active_created", "users", ["is_active", "created_at"])

    op.create_table(
        "admins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("credential_version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("credential_version >= 1", name="ck_admins_credential_version_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        comment="B 端管理员账户",
    )
    op.create_index("ix_admins_active_created", "admins", ["is_active", "created_at"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False, comment="稳定角色代码"),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        comment="管理员角色",
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=150), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("catalog_version", sa.String(length=64), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        comment="源码权限目录数据库映射",
    )
    op.create_table(
        "admin_roles",
        sa.Column("admin_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("admin_id", "role_id"),
        comment="管理员与角色关联",
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        comment="角色与权限关联",
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="用户 ID"),
        sa.Column("family_id", sa.Uuid(), nullable=False, comment="Refresh Token 族 ID"),
        sa.Column("credential_profile", sa.String(length=32), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column("csrf_digest", sa.String(length=64), nullable=False, comment="CSRF Token HMAC"),
        sa.Column("ip_address", postgresql.INET(), nullable=True, comment="可信客户端 IP"),
        sa.Column("user_agent_summary", sa.String(length=512), nullable=True, comment="清理后的 UA 摘要"),
        sa.Column("device_name", sa.String(length=100), nullable=True, comment="设备展示名称"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("credential_profile = 'browser_cookie'", name="ck_user_sessions_profile"),
        sa.CheckConstraint("idle_expires_at <= absolute_expires_at", name="ck_user_sessions_expiry_order"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        comment="C 端登录会话权威记录",
    )
    op.create_index("ix_user_sessions_family_id", "user_sessions", ["family_id"])
    op.create_index("ix_user_sessions_user_active", "user_sessions", ["user_id", "revoked_at", "absolute_expires_at"])

    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=False, comment="管理员 ID"),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("credential_profile", sa.String(length=32), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column("csrf_digest", sa.String(length=64), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent_summary", sa.String(length=512), nullable=True),
        sa.Column("device_name", sa.String(length=100), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("credential_profile = 'browser_cookie'", name="ck_admin_sessions_profile"),
        sa.CheckConstraint("idle_expires_at <= absolute_expires_at", name="ck_admin_sessions_expiry_order"),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        comment="B 端管理员登录会话权威记录",
    )
    op.create_index("ix_admin_sessions_family_id", "admin_sessions", ["family_id"])
    op.create_index(
        "ix_admin_sessions_admin_active", "admin_sessions", ["admin_id", "revoked_at", "absolute_expires_at"]
    )

    op.create_table(
        "user_refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False, comment="Token HMAC"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=64), nullable=True),
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["replaced_by_id"], ["user_refresh_tokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["user_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_digest"),
        comment="C 端 Refresh Token 单次消费记录",
    )
    op.create_index("ix_user_refresh_session_state", "user_refresh_tokens", ["session_id", "consumed_at", "revoked_at"])
    op.create_table(
        "admin_refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=64), nullable=True),
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["replaced_by_id"], ["admin_refresh_tokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["admin_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_digest"),
        comment="B 端 Refresh Token 单次消费记录",
    )
    op.create_index(
        "ix_admin_refresh_session_state", "admin_refresh_tokens", ["session_id", "consumed_at", "revoked_at"]
    )

    op.create_table(
        "security_login_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_type", sa.String(length=16), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=True),
        sa.Column("identifier_digest", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent_summary", sa.String(length=512), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("release_version", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("principal_type IN ('user', 'admin')", name="ck_login_events_principal_type"),
        sa.PrimaryKeyConstraint("id"),
        comment="登录、刷新和会话安全事件",
    )
    op.create_index("ix_login_events_occurred", "security_login_events", ["occurred_at"])
    op.create_index(
        "ix_login_events_principal",
        "security_login_events",
        ["principal_type", "principal_id", "occurred_at"],
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("changed_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("release_version", sa.String(length=128), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("result IN ('started', 'succeeded', 'denied', 'failed')", name="ck_audit_events_result"),
        sa.PrimaryKeyConstraint("id"),
        comment="高风险管理操作审计事件",
    )
    op.create_index("ix_audit_events_occurred", "audit_events", ["occurred_at"])
    op.create_index("ix_audit_events_actor_action", "audit_events", ["actor_id", "action", "occurred_at"])

    op.create_table(
        "request_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("route_template", sa.String(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False),
        sa.Column("principal_type", sa.String(length=16), nullable=True),
        sa.Column("principal_digest", sa.String(length=64), nullable=True),
        sa.Column("release_version", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("duration_ms >= 0", name="ck_request_logs_duration_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
        comment="可选请求元数据日志，不保存正文和凭据",
    )
    op.create_index("ix_request_logs_occurred", "request_logs", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_request_logs_occurred", table_name="request_logs")
    op.drop_table("request_logs")
    op.drop_index("ix_audit_events_actor_action", table_name="audit_events")
    op.drop_index("ix_audit_events_occurred", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_login_events_principal", table_name="security_login_events")
    op.drop_index("ix_login_events_occurred", table_name="security_login_events")
    op.drop_table("security_login_events")
    op.drop_index("ix_admin_refresh_session_state", table_name="admin_refresh_tokens")
    op.drop_table("admin_refresh_tokens")
    op.drop_index("ix_user_refresh_session_state", table_name="user_refresh_tokens")
    op.drop_table("user_refresh_tokens")
    op.drop_index("ix_admin_sessions_admin_active", table_name="admin_sessions")
    op.drop_index("ix_admin_sessions_family_id", table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_index("ix_user_sessions_user_active", table_name="user_sessions")
    op.drop_index("ix_user_sessions_family_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("role_permissions")
    op.drop_table("admin_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index("ix_admins_active_created", table_name="admins")
    op.drop_table("admins")
    op.drop_index("ix_users_active_created", table_name="users")
    op.drop_table("users")
