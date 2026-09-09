"""Align user soft-delete column comments with the current model.

Revision ID: 20260829_01
Revises: 20260828_01
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260829_01"
down_revision: str | None = "20260828_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "deleted_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        comment="软删除时间，非空表示已进入回收站",
    )
    op.alter_column(
        "users",
        "deletion_reason",
        existing_type=sa.String(length=100),
        existing_nullable=True,
        comment="软删除原因，可为空",
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "deleted_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        comment="注销时间",
    )
    op.alter_column(
        "users",
        "deletion_reason",
        existing_type=sa.String(length=100),
        existing_nullable=True,
        comment="账户删除原因代码",
    )
