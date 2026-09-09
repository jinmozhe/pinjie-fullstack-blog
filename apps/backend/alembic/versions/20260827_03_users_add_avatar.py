"""Add user avatar binding path.

Revision ID: 20260827_03
Revises: 20260827_02
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260827_03"
down_revision: str | None = "20260827_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar", sa.String(length=500), nullable=True, comment="用户头像站内资源路径"))


def downgrade() -> None:
    op.drop_column("users", "avatar")
