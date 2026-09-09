"""Add sanitized error request body to request logs.

Revision ID: 20260820_01
Revises: 20260815_01
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260820_01"
down_revision: str | None = "20260815_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "request_logs",
        sa.Column("request_body", sa.Text(), nullable=True, comment="脱敏后的错误请求入参"),
    )
    op.execute("COMMENT ON TABLE request_logs IS '可选请求元数据日志，仅保存脱敏后的错误请求入参'")


def downgrade() -> None:
    op.execute("COMMENT ON TABLE request_logs IS '可选请求元数据日志，不保存正文和凭据'")
    op.drop_column("request_logs", "request_body")
