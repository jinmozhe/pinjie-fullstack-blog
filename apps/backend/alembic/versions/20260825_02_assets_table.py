"""Create unified file asset metadata table.

Revision ID: 20260825_02
Revises: 20260825_01
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260825_02"
down_revision: str | None = "20260825_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("uploader_type", sa.String(length=20), nullable=False, comment="上传主体类型"),
        sa.Column("uploader_id", sa.Uuid(), nullable=True, comment="上传主体 ID，系统任务可为空"),
        sa.Column("storage_driver", sa.String(length=20), nullable=False, comment="存储驱动代码"),
        sa.Column("file_key", sa.String(length=500), nullable=False, comment="存储相对文件键"),
        sa.Column("original_name", sa.String(length=255), nullable=False, comment="上传原始文件名"),
        sa.Column("mime_type", sa.String(length=100), nullable=False, comment="探测得到的真实 MIME 类型"),
        sa.Column("file_size", sa.BigInteger(), nullable=False, comment="文件字节数"),
        sa.Column("file_hash", sa.String(length=64), nullable=False, comment="SHA-256 内容哈希"),
        sa.Column("url", sa.String(length=1000), nullable=False, comment="公开访问 URL 或站内路径"),
        sa.Column("scene", sa.String(length=50), nullable=False, comment="受控文件使用场景"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("char_length(file_hash) = 64", name="ck_assets_file_hash_length"),
        sa.CheckConstraint("file_size > 0", name="ck_assets_file_size_positive"),
        sa.CheckConstraint("storage_driver IN ('local')", name="ck_assets_storage_driver"),
        sa.CheckConstraint("uploader_type IN ('admin', 'user', 'system')", name="ck_assets_uploader_type"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_key", name="uq_assets_file_key"),
        sa.UniqueConstraint(
            "uploader_type",
            "uploader_id",
            "scene",
            "file_hash",
            name="uq_assets_uploader_scene_hash",
        ),
        comment="统一文件与多媒体资产元数据",
    )
    op.create_index("ix_assets_created", "assets", ["created_at"])
    op.create_index("ix_assets_scene_created", "assets", ["scene", "created_at"])
    op.create_index("ix_assets_uploader_created", "assets", ["uploader_type", "uploader_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_assets_uploader_created", table_name="assets")
    op.drop_index("ix_assets_scene_created", table_name="assets")
    op.drop_index("ix_assets_created", table_name="assets")
    op.drop_table("assets")
