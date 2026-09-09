"""Add avatar field to admins table.

Revision ID: 20260825_01
Revises: 20260820_01
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260825_01"
down_revision: str | None = "20260820_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "admins",
        sa.Column("avatar", sa.String(length=500), nullable=True, comment="管理员头像 URL 或路径"),
    )


def downgrade() -> None:
    op.drop_column("admins", "avatar")
