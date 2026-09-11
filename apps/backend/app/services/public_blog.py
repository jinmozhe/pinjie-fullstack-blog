import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.models import Post
from app.db.repositories.asset import AssetRepository
from app.db.repositories.blog import BlogRepository, TaxonomyName
from app.db.repositories.public_blog import PublicBlogRepository
from app.domains.blog.public_schemas import (
    PublicPostPage,
    PublicPostQuery,
    PublicPostRead,
    PublicPostSummary,
    PublicTaxonomy,
    PublicTaxonomyCount,
    PublicTaxonomyPage,
)
from app.domains.blog.rules import render_markdown

T = TypeVar("T")


class PublicBlogService:
    def __init__(self, *, session: AsyncSession, settings: Settings) -> None:
        self._repository = PublicBlogRepository(session)
        self._content = BlogRepository(session)
        self._assets = AssetRepository(session)
        self._settings = settings

    async def _database(self, operation: Callable[[], Awaitable[T]]) -> T:
        try:
            return await operation()
        except SQLAlchemyError as exc:
            raise AppException(
                status_code=503, code=ErrorCode.SERVICE_UNAVAILABLE, message="文章服务暂时不可用，请稍后重试"
            ) from exc

    async def _present(self, posts: list[Post]) -> list[PublicPostSummary]:
        categories = await self._content.taxonomy("categories", [p.category_id for p in posts if p.category_id])
        category_map = {row.id: PublicTaxonomy(name=row.name, slug=row.slug) for row in categories}
        tags = await self._content.tags_for_posts([p.id for p in posts])
        covers = await self._assets.get_many([p.cover_asset_id for p in posts if p.cover_asset_id])
        cover_map = {row.id: row.url for row in covers}
        return [
            PublicPostSummary(
                title=post.title,
                slug=post.slug,
                summary=post.summary,
                category=category_map.get(post.category_id) if post.category_id else None,
                tags=[PublicTaxonomy(name=tag.name, slug=tag.slug) for tag in tags.get(post.id, [])],
                cover_url=cover_map.get(post.cover_asset_id) if post.cover_asset_id else None,
                published_at=post.published_at,
                updated_at=post.updated_at,
            )
            for post in posts
        ]

    async def list_posts(self, query: PublicPostQuery) -> PublicPostPage:
        async def operation() -> PublicPostPage:
            posts, total = await self._repository.list_posts(
                page=query.page, page_size=query.page_size, q=query.q, category=query.category, tag=query.tag
            )
            return PublicPostPage.create(
                items=await self._present(posts), total=total, page=query.page, page_size=query.page_size
            )

        return await self._database(operation)

    async def get_post(self, slug: str) -> PublicPostRead:
        async def operation() -> PublicPostRead:
            post = await self._repository.get_post(slug)
            if post is None:
                raise AppException(status_code=404, code=ErrorCode.NOT_FOUND, message="文章不存在")
            summary = (await self._present([post]))[0]
            rendered = await asyncio.to_thread(
                render_markdown, post.markdown, upload_base_url=self._settings.upload_base_url
            )
            return PublicPostRead(**summary.model_dump(), html=rendered.html)

        return await self._database(operation)

    async def list_taxonomy(self, kind: TaxonomyName, *, page: int, page_size: int) -> PublicTaxonomyPage:
        async def operation() -> PublicTaxonomyPage:
            rows, total = await self._repository.taxonomy(kind, page=page, page_size=page_size)
            return PublicTaxonomyPage.create(
                items=[PublicTaxonomyCount(name=row.name, slug=row.slug, post_count=count) for row, count in rows],
                total=total,
                page=page,
                page_size=page_size,
            )

        return await self._database(operation)

    async def get_taxonomy(self, kind: TaxonomyName, slug: str) -> PublicTaxonomyCount:
        async def operation() -> PublicTaxonomyCount:
            rows, _ = await self._repository.taxonomy(kind, page=1, page_size=1, slug=slug)
            if not rows:
                raise AppException(status_code=404, code=ErrorCode.NOT_FOUND, message="分类或标签不存在")
            row, count = rows[0]
            return PublicTaxonomyCount(name=row.name, slug=row.slug, post_count=count)

        return await self._database(operation)
