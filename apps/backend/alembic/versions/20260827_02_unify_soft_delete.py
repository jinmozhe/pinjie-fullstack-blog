"""Unify soft-delete lifecycle fields and remove anonymization.

Revision ID: 20260827_02
Revises: 20260827_01
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260827_02"
down_revision: str | None = "20260827_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SYSTEM_ACTOR_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_by_id", sa.Uuid(), nullable=True, comment="执行软删除的主体 ID"))
    op.add_column(
        "users",
        sa.Column("deleted_by_type", sa.String(length=16), nullable=True, comment="执行软删除的主体类型"),
    )
    op.execute(
        "UPDATE users SET deleted_by_id = deleted_by_admin_id, deleted_by_type = 'admin' "
        "WHERE deleted_at IS NOT NULL AND deleted_by_admin_id IS NOT NULL"
    )
    op.execute(
        "UPDATE users SET deleted_by_id = id, deleted_by_type = 'user' "
        "WHERE deleted_at IS NOT NULL AND deleted_by_id IS NULL AND deletion_reason = 'self_deleted'"
    )
    op.execute(
        f"UPDATE users SET deleted_by_id = '{_SYSTEM_ACTOR_ID}'::uuid, deleted_by_type = 'system' "
        "WHERE deleted_at IS NOT NULL AND deleted_by_id IS NULL"
    )
    op.drop_constraint("fk_users_deleted_by_admin_id_admins", "users", type_="foreignkey")
    op.drop_index("ix_users_deleted_anonymized", table_name="users")
    op.drop_column("users", "deleted_by_admin_id")
    op.drop_column("users", "anonymized_at")
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])
    op.create_check_constraint(
        "ck_users_soft_delete_actor_consistency",
        "users",
        "(deleted_at IS NULL AND deleted_by_id IS NULL AND deleted_by_type IS NULL) "
        "OR (deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL AND deleted_by_type IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_users_soft_delete_actor_type",
        "users",
        "deleted_by_type IS NULL OR deleted_by_type IN ('admin', 'user', 'system')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_soft_delete_actor_type", "users", type_="check")
    op.drop_constraint("ck_users_soft_delete_actor_consistency", "users", type_="check")
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.add_column("users", sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("deleted_by_admin_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_users_deleted_by_admin_id_admins",
        "users",
        "admins",
        ["deleted_by_admin_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("UPDATE users SET deleted_by_admin_id = deleted_by_id WHERE deleted_by_type = 'admin'")
    op.drop_column("users", "deleted_by_type")
    op.drop_column("users", "deleted_by_id")
    op.create_index("ix_users_deleted_anonymized", "users", ["deleted_at", "anonymized_at"])
