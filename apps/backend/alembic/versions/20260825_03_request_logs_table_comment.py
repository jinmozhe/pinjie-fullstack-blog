"""Align the request log table comment with captured request bodies.

Revision ID: 20260825_03
Revises: 20260825_02
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260825_03"
down_revision: str | None = "20260825_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_COMMENT = "可选请求元数据日志，不保存正文和凭据"
_NEW_COMMENT = "可选请求元数据日志，仅保存脱敏后的错误请求入参"


def upgrade() -> None:
    op.create_table_comment(
        "request_logs",
        _NEW_COMMENT,
        existing_comment=_OLD_COMMENT,
    )


def downgrade() -> None:
    op.create_table_comment(
        "request_logs",
        _OLD_COMMENT,
        existing_comment=_NEW_COMMENT,
    )
