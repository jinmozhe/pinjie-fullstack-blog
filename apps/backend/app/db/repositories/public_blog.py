"""请求时读取公开内容的只读模型，所有入口包含相同的可见性过滤。"""

from typing import cast

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import Category, Post, PostTag, Tag
from app.db.repositories.blog import TaxonomyModel, TaxonomyName


def public_post_predicates() -> tuple[ColumnElement[bool], ColumnElement[bool]]:
    return Post.status == "public", Post.deleted_at.is_(None)


class PublicBlogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_posts(
        self, *, page: int, page_size: int, q: str, category: str | None, tag: str | None
    ) -> tuple[list[Post], int]:
        filters = list(public_post_predicates())
        if q:
            filters.append(or_(Post.title.icontains(q, autoescape=True), Post.summary.icontains(q, autoescape=True)))
        if category:
            filters.append(Post.category_id.in_(select(Category.id).where(Category.slug == category)))
        if tag:
            filters.append(
                Post.id.in_(select(PostTag.post_id).join(Tag, Tag.id == PostTag.tag_id).where(Tag.slug == tag))
            )
        total = int((await self._session.scalars(select(func.count()).select_from(Post).where(*filters))).one())
        rows = await self._session.scalars(
            select(Post)
            .options(defer(Post.markdown))
            .where(*filters)
            .order_by(Post.published_at.desc(), Post.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows), total

    async def get_post(self, slug: str) -> Post | None:
        return (
            await self._session.scalars(select(Post).where(*public_post_predicates(), Post.slug == slug))
        ).one_or_none()

    async def taxonomy(
        self, kind: TaxonomyName, *, page: int, page_size: int, slug: str | None = None
    ) -> tuple[list[tuple[TaxonomyModel, int]], int]:
        model = Category if kind == "categories" else Tag
        counts = (
            select(Post.category_id.label("taxonomy_id"), func.count().label("post_count"))
            .where(*public_post_predicates())
            .group_by(Post.category_id)
            if kind == "categories"
            else select(PostTag.tag_id.label("taxonomy_id"), func.count().label("post_count"))
            .join(Post, Post.id == PostTag.post_id)
            .where(*public_post_predicates())
            .group_by(PostTag.tag_id)
        ).subquery()
        statement = select(model, counts.c.post_count).join(counts, model.id == counts.c.taxonomy_id)
        if slug is not None:
            statement = statement.where(model.slug == slug)
        total = int((await self._session.scalars(select(func.count()).select_from(statement.subquery()))).one())
        rows = await self._session.execute(
            statement.order_by(model.name, model.id).offset((page - 1) * page_size).limit(page_size)
        )
        return [(cast(TaxonomyModel, row[0]), int(row[1])) for row in rows], total
