"""Add recoverable user recycle-bin lifecycle fields.

Revision ID: 20260827_01
Revises: 20260825_03
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260827_01"
down_revision: str | None = "20260825_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("deleted_by_admin_id", sa.Uuid(), nullable=True, comment="执行软删除的管理员 ID"),
    )
    op.add_column(
        "users",
        sa.Column("deletion_reason", sa.String(length=100), nullable=True, comment="账户删除原因代码"),
    )
    op.add_column(
        "users",
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True, comment="身份资料永久匿名化时间"),
    )
    op.create_foreign_key(
        "fk_users_deleted_by_admin_id_admins",
        "users",
        "admins",
        ["deleted_by_admin_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_deleted_anonymized", "users", ["deleted_at", "anonymized_at"])
    op.execute(
        "UPDATE users SET anonymized_at = deleted_at, deletion_reason = 'legacy_anonymized' "
        "WHERE deleted_at IS NOT NULL"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET "
        "username = 'deleted-' || substr(replace(id::text, '-', ''), 1, 24) || '-' || "
        "substr(md5(random()::text || id::text), 1, 16), "
        "email = NULL, display_name = NULL "
        "WHERE deleted_at IS NOT NULL AND anonymized_at IS NULL"
    )
    op.drop_index("ix_users_deleted_anonymized", table_name="users")
    op.drop_constraint("fk_users_deleted_by_admin_id_admins", "users", type_="foreignkey")
    op.drop_column("users", "anonymized_at")
    op.drop_column("users", "deletion_reason")
    op.drop_column("users", "deleted_by_admin_id")
