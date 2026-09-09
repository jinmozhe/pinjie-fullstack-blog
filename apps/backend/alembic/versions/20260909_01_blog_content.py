"""Add current blog content, taxonomy and protected asset references.

Revision ID: 20260909_01
Revises: 20260829_01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260909_01"
down_revision: str | None = "20260829_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(80), nullable=False, comment="分类名称"),
        sa.Column("slug", sa.String(120), nullable=False, comment="分类唯一标识"),
        sa.Column("revision", sa.Integer(), nullable=False, comment="并发修改校验号"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
        sa.CheckConstraint("revision > 0", name="ck_categories_revision"),
        comment="博客文章分类，每篇文章最多一个分类",
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(80), nullable=False, comment="标签名称"),
        sa.Column("slug", sa.String(120), nullable=False, comment="标签唯一标识"),
        sa.Column("revision", sa.Integer(), nullable=False, comment="并发修改校验号"),
        sa.UniqueConstraint("name", name="uq_tags_name"),
        sa.UniqueConstraint("slug", name="uq_tags_slug"),
        sa.CheckConstraint("revision > 0", name="ck_tags_revision"),
        comment="博客文章标签",
    )
    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="软删除时间，非空表示已进入回收站"),
        sa.Column("deleted_by_id", sa.Uuid(), nullable=True, comment="执行软删除的主体 ID"),
        sa.Column("deleted_by_type", sa.String(16), nullable=True, comment="执行软删除的主体类型"),
        sa.Column("deletion_reason", sa.String(100), nullable=True, comment="软删除原因，可为空"),
        sa.Column("title", sa.String(200), nullable=False, comment="文章标题"),
        sa.Column("slug", sa.String(120), nullable=False, comment="首次发布后固定且回收站继续占用的网址标识"),
        sa.Column("summary", sa.String(500), nullable=False, comment="可选文章摘要"),
        sa.Column("markdown", sa.Text(), nullable=False, comment="Markdown 当前正文，不保留历史版本"),
        sa.Column("status", sa.String(16), nullable=False, comment="public 公开或 hidden 隐藏"),
        sa.Column(
            "category_id",
            sa.Uuid(),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=True,
            comment="可空分类",
        ),
        sa.Column(
            "cover_asset_id",
            sa.Uuid(),
            sa.ForeignKey("assets.id", ondelete="RESTRICT"),
            nullable=True,
            comment="可空封面资产，删除前必须解除引用",
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, comment="服务端生成的首次发布时间，UTC"),
        sa.Column("revision", sa.Integer(), nullable=False, comment="并发修改校验号，不代表历史版本"),
        sa.UniqueConstraint("slug", name="uq_posts_slug"),
        sa.CheckConstraint("status IN ('public', 'hidden')", name="ck_posts_status"),
        sa.CheckConstraint("revision > 0", name="ck_posts_revision"),
        comment="博客当前文章，软删除与公开状态独立",
    )
    op.create_index("ix_posts_deleted_at", "posts", ["deleted_at"])
    op.create_index("ix_posts_reading", "posts", ["deleted_at", "status", "published_at", "id"])
    op.create_index("ix_posts_category", "posts", ["category_id"])
    op.create_table(
        "post_tags",
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("posts.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("tag_id", sa.Uuid(), sa.ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True),
        comment="文章与标签关联，覆盖回收站文章",
    )
    op.create_index("ix_post_tags_tag", "post_tags", ["tag_id"])
    op.create_table(
        "post_assets",
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("posts.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("assets.id", ondelete="RESTRICT"), primary_key=True),
        comment="正文与封面资产引用，隐藏及软删除仍保留",
    )
    op.create_index("ix_post_assets_asset", "post_assets", ["asset_id"])


def downgrade() -> None:
    raise RuntimeError("博客内容迁移禁止自动删表降级，请使用经授权的数据库备份恢复或前向修复")
