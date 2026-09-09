"""博客当前内容及其关联，不保存历史正文。"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("name", name="uq_categories_name"),
        UniqueConstraint("slug", name="uq_categories_slug"),
        CheckConstraint("revision > 0", name="ck_categories_revision"),
        {"comment": "博客文章分类，每篇文章最多一个分类"},
    )
    name: Mapped[str] = mapped_column(String(80), comment="分类名称")
    slug: Mapped[str] = mapped_column(String(120), comment="分类唯一标识")
    revision: Mapped[int] = mapped_column(Integer, default=1, comment="并发修改校验号")


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name"),
        UniqueConstraint("slug", name="uq_tags_slug"),
        CheckConstraint("revision > 0", name="ck_tags_revision"),
        {"comment": "博客文章标签"},
    )
    name: Mapped[str] = mapped_column(String(80), comment="标签名称")
    slug: Mapped[str] = mapped_column(String(120), comment="标签唯一标识")
    revision: Mapped[int] = mapped_column(Integer, default=1, comment="并发修改校验号")


class Post(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_posts_slug"),
        CheckConstraint("status IN ('public', 'hidden')", name="ck_posts_status"),
        CheckConstraint("revision > 0", name="ck_posts_revision"),
        Index("ix_posts_reading", "deleted_at", "status", "published_at", "id"),
        Index("ix_posts_category", "category_id"),
        {"comment": "博客当前文章，软删除与公开状态独立"},
    )
    title: Mapped[str] = mapped_column(String(200), comment="文章标题")
    slug: Mapped[str] = mapped_column(String(120), comment="首次发布后固定且回收站继续占用的网址标识")
    summary: Mapped[str] = mapped_column(String(500), default="", comment="可选文章摘要")
    markdown: Mapped[str] = mapped_column(Text, comment="Markdown 当前正文，不保留历史版本")
    status: Mapped[str] = mapped_column(String(16), default="public", comment="public 公开或 hidden 隐藏")
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True, comment="可空分类"
    )
    cover_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"), nullable=True, comment="可空封面资产，删除前必须解除引用"
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), comment="服务端生成的首次发布时间，UTC")
    revision: Mapped[int] = mapped_column(Integer, default=1, comment="并发修改校验号，不代表历史版本")


class PostTag(Base):
    __tablename__ = "post_tags"
    __table_args__ = (Index("ix_post_tags_tag", "tag_id"), {"comment": "文章与标签关联，覆盖回收站文章"})
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="RESTRICT"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True)


class PostAsset(Base):
    __tablename__ = "post_assets"
    __table_args__ = (Index("ix_post_assets_asset", "asset_id"), {"comment": "正文与封面资产引用，隐藏及软删除仍保留"})
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="RESTRICT"), primary_key=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"), primary_key=True)
