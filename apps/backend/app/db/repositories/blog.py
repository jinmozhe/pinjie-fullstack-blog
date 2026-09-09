import uuid
from datetime import datetime
from typing import Literal, cast

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import Category, Post, PostAsset, PostTag, Tag

TaxonomyModel = Category | Tag
TaxonomyName = Literal["categories", "tags"]


class BlogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lock_content(self) -> None:
        # A single writer owns taxonomy membership and post revision changes.
        # Asset writers use their own row locks and never wait on this lock.
        await self.session.execute(select(func.set_config("lock_timeout", "5000", True)))
        await self.session.execute(select(func.pg_advisory_xact_lock(20260909, 1)))

    def add(self, entity: Post | Category | Tag) -> None:
        self.session.add(entity)

    async def flush(self) -> None:
        await self.session.flush()

    async def get_post(self, post_id: uuid.UUID, *, lock: bool = False) -> Post | None:
        query = select(Post).where(Post.id == post_id).execution_options(populate_existing=True)
        if lock:
            query = query.with_for_update()
        return (await self.session.scalars(query)).one_or_none()

    async def posts_by_ids(self, ids: list[uuid.UUID], *, lock: bool = False) -> list[Post]:
        query = select(Post).where(Post.id.in_(ids)).order_by(Post.id).execution_options(populate_existing=True)
        if lock:
            query = query.with_for_update()
        return list(await self.session.scalars(query))

    async def list_posts(
        self,
        *,
        page: int,
        page_size: int,
        deleted: bool,
        status: str | None,
        category_id: uuid.UUID | None,
        tag_id: uuid.UUID | None,
        published_from: datetime | None,
        published_until: datetime | None,
    ) -> tuple[list[Post], int]:
        filters: list[ColumnElement[bool]] = [Post.deleted_at.is_not(None) if deleted else Post.deleted_at.is_(None)]
        if status:
            filters.append(Post.status == status)
        if category_id:
            filters.append(Post.category_id == category_id)
        if tag_id:
            filters.append(Post.id.in_(select(PostTag.post_id).where(PostTag.tag_id == tag_id)))
        if published_from:
            filters.append(Post.published_at >= published_from)
        if published_until:
            filters.append(Post.published_at < published_until)
        total = await self.session.scalar(select(func.count()).select_from(Post).where(*filters))
        posts = await self.session.scalars(
            select(Post)
            .where(*filters)
            .order_by(Post.published_at.desc(), Post.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(posts), int(total or 0)

    async def taxonomy(self, kind: TaxonomyName, ids: list[uuid.UUID], *, lock: bool = False) -> list[TaxonomyModel]:
        model: type[Category] | type[Tag] = Category if kind == "categories" else Tag
        query = select(model).where(model.id.in_(ids)).order_by(model.id).execution_options(populate_existing=True)
        if lock:
            query = query.with_for_update()
        # SQLAlchemy widens the selected union to Base; model is restricted above.
        return [cast(TaxonomyModel, row) for row in await self.session.scalars(query)]

    async def list_taxonomy(self, kind: TaxonomyName, *, page: int, page_size: int) -> tuple[list[TaxonomyModel], int]:
        model: type[Category] | type[Tag] = Category if kind == "categories" else Tag
        total = await self.session.scalar(select(func.count()).select_from(model))
        rows = await self.session.scalars(
            select(model).order_by(model.name, model.id).offset((page - 1) * page_size).limit(page_size)
        )
        return [cast(TaxonomyModel, row) for row in rows], int(total or 0)

    async def tags_for_posts(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, list[Tag]]:
        rows = await self.session.execute(
            select(PostTag.post_id, Tag)
            .join(Tag, Tag.id == PostTag.tag_id)
            .where(PostTag.post_id.in_(ids))
            .order_by(Tag.name, Tag.id)
        )
        result: dict[uuid.UUID, list[Tag]] = {}
        for post_id, tag in rows:
            result.setdefault(post_id, []).append(tag)
        return result

    async def asset_ids(self, post_id: uuid.UUID) -> list[uuid.UUID]:
        return list(await self.session.scalars(select(PostAsset.asset_id).where(PostAsset.post_id == post_id)))

    async def replace_tags(self, post_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> None:
        await self.session.execute(delete(PostTag).where(PostTag.post_id == post_id))
        self.session.add_all(PostTag(post_id=post_id, tag_id=tag_id) for tag_id in tag_ids)

    async def replace_assets(self, post_id: uuid.UUID, asset_ids: list[uuid.UUID]) -> None:
        await self.session.execute(delete(PostAsset).where(PostAsset.post_id == post_id))
        self.session.add_all(PostAsset(post_id=post_id, asset_id=asset_id) for asset_id in asset_ids)

    async def affected_posts(self, kind: TaxonomyName, ids: list[uuid.UUID]) -> list[Post]:
        predicate = (
            Post.category_id.in_(ids)
            if kind == "categories"
            else Post.id.in_(select(PostTag.post_id).where(PostTag.tag_id.in_(ids)))
        )
        return list(
            await self.session.scalars(
                select(Post).where(predicate).order_by(Post.id).execution_options(populate_existing=True)
            )
        )

    async def delete_taxonomy(self, kind: TaxonomyName, ids: list[uuid.UUID]) -> None:
        if kind == "tags":
            await self.session.execute(delete(PostTag).where(PostTag.tag_id.in_(ids)))
        await self.session.flush()
        model = Category if kind == "categories" else Tag
        await self.session.execute(delete(model).where(model.id.in_(ids)))
