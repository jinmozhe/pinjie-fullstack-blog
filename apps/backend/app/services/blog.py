from __future__ import annotations

import asyncio
import hmac
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.identifiers import new_uuid7
from app.core.request_metadata import RequestMetadata
from app.db.models import Category, Post, Tag
from app.db.repositories.asset import AssetRepository
from app.db.repositories.blog import BlogRepository, TaxonomyModel, TaxonomyName
from app.domains.blog.rules import (
    RenderedMarkdown,
    confirmation_digest,
    publication_range,
    render_markdown,
    require_lifecycle,
    require_revision,
)
from app.domains.blog.schemas import (
    BlogBatchResult,
    MarkdownPreview,
    PostBatch,
    PostContent,
    PostCreate,
    PostListQuery,
    PostPage,
    PostRead,
    PostStatus,
    PostStatusUpdate,
    PostSummary,
    PostTarget,
    PostUpdate,
    TaxonomyCreate,
    TaxonomyDelete,
    TaxonomyImpact,
    TaxonomyPage,
    TaxonomyRead,
    TaxonomyUpdate,
)
from app.services.security_events import AuditCoordinator

T = TypeVar("T")


class BlogService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
        metadata: RequestMetadata,
        actor_id: uuid.UUID,
    ) -> None:
        self._repository = BlogRepository(session)
        self._assets = AssetRepository(session)
        self._settings = settings
        self._actor_id = actor_id
        self._audit_coordinator = AuditCoordinator(
            session=session, session_factory=session_factory, actor_id=actor_id, metadata=metadata
        )

    async def _database(self, operation: Callable[[], Awaitable[T]]) -> T:
        try:
            return await operation()
        except IntegrityError as exc:
            constraint = getattr(getattr(exc.orig, "__cause__", None), "constraint_name", None)
            if constraint in {
                "uq_posts_slug",
                "uq_categories_name",
                "uq_categories_slug",
                "uq_tags_name",
                "uq_tags_slug",
            }:
                raise AppException(
                    status_code=409,
                    code=ErrorCode.BLOG_IDENTITY_CONFLICT,
                    message="名称或网址标识已被占用；回收站文章仍占用原网址",
                ) from exc
            raise AppException(
                status_code=503, code=ErrorCode.SERVICE_UNAVAILABLE, message="内容服务暂时不可用，请刷新后核对操作结果"
            ) from exc
        except SQLAlchemyError as exc:
            raise AppException(
                status_code=503, code=ErrorCode.SERVICE_UNAVAILABLE, message="内容服务暂时不可用，请刷新后核对操作结果"
            ) from exc

    async def _write(
        self,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None,
        fields: dict[str, object],
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        async def locked_operation() -> T:
            await self._repository.lock_content()
            return await operation()

        return await self._database(
            lambda: self._audit_coordinator.execute(
                action=action,
                target_type=target_type,
                target_id=target_id,
                changed_fields=fields,
                operation=locked_operation,
            )
        )

    async def preview(self, markdown: str) -> MarkdownPreview:
        rendered = await self._render(markdown)
        return MarkdownPreview(html=rendered.html)

    async def _render(self, markdown: str) -> RenderedMarkdown:
        return await asyncio.to_thread(render_markdown, markdown, upload_base_url=self._settings.upload_base_url)

    async def list_posts(self, query: PostListQuery) -> PostPage:
        async def operation() -> PostPage:
            start, until = publication_range(query.published_from, query.published_to)
            rows, total = await self._repository.list_posts(
                page=query.page,
                page_size=query.page_size,
                deleted=query.deleted,
                status=query.status,
                category_id=query.category_id,
                tag_id=query.tag_id,
                published_from=start,
                published_until=until,
            )
            details = await self._present(rows)
            return PostPage.create(
                items=[PostSummary(**item.model_dump(exclude={"markdown"})) for item in details],
                page=query.page,
                page_size=query.page_size,
                total=total,
            )

        return await self._database(operation)

    async def get_post(self, post_id: uuid.UUID) -> PostRead:
        async def operation() -> PostRead:
            return (await self._present([await self._require_post(post_id)]))[0]

        return await self._database(operation)

    async def _require_post(self, post_id: uuid.UUID, *, lock: bool = False) -> Post:
        post = await self._repository.get_post(post_id, lock=lock)
        if post is None:
            raise AppException(status_code=404, code=ErrorCode.BLOG_NOT_FOUND, message="文章不存在")
        return post

    async def _present(self, posts: list[Post]) -> list[PostRead]:
        categories = await self._repository.taxonomy(
            "categories", list({post.category_id for post in posts if post.category_id})
        )
        category_map = {item.id: TaxonomyRead.model_validate(item) for item in categories}
        tags = await self._repository.tags_for_posts([post.id for post in posts])
        covers = await self._assets.get_many(list({post.cover_asset_id for post in posts if post.cover_asset_id}))
        cover_map = {asset.id: asset.url for asset in covers}
        return [
            PostRead(
                id=post.id,
                title=post.title,
                slug=post.slug,
                summary=post.summary,
                markdown=post.markdown,
                status=PostStatus(post.status),
                category=category_map.get(post.category_id) if post.category_id else None,
                tags=[TaxonomyRead.model_validate(tag) for tag in tags.get(post.id, [])],
                cover_asset_id=post.cover_asset_id,
                cover_url=cover_map.get(post.cover_asset_id) if post.cover_asset_id else None,
                published_at=post.published_at,
                updated_at=post.updated_at,
                deleted_at=post.deleted_at,
                revision=post.revision,
            )
            for post in posts
        ]

    async def _validate_content(
        self, payload: PostContent, rendered: RenderedMarkdown, *, post_id: uuid.UUID | None = None
    ) -> list[uuid.UUID]:
        if payload.category_id and not await self._repository.taxonomy("categories", [payload.category_id], lock=True):
            raise AppException(status_code=404, code=ErrorCode.BLOG_NOT_FOUND, message="分类已不存在，请重新选择")
        tags = await self._repository.taxonomy("tags", payload.tag_ids, lock=True)
        if len(tags) != len(payload.tag_ids):
            raise AppException(
                status_code=404, code=ErrorCode.BLOG_NOT_FOUND, message="一个或多个标签已不存在，请重新选择"
            )
        images = await self._assets.get_by_urls(list(rendered.image_paths))
        if {image.url for image in images} != rendered.image_paths:
            raise AppException(
                status_code=422, code=ErrorCode.BLOG_MEDIA_INVALID, message="正文引用了不存在或已删除的图片"
            )
        current = {image.id for image in images}
        if payload.cover_asset_id:
            current.add(payload.cover_asset_id)
        old = set(await self._repository.asset_ids(post_id)) if post_id else set()
        # Keep old and new asset locks until the article and references commit.
        locked = await self._assets.get_many(sorted(current | old), for_update=True)
        if {asset.id for asset in locked} != current | old:
            raise AppException(status_code=422, code=ErrorCode.BLOG_MEDIA_INVALID, message="图片已被删除，请重新上传")
        if any(
            asset.id in current
            and (asset.scene != "article" or asset.uploader_type != "admin" or not asset.mime_type.startswith("image/"))
            for asset in locked
        ):
            raise AppException(
                status_code=422, code=ErrorCode.BLOG_MEDIA_INVALID, message="正文和封面只能使用管理员上传的文章图片"
            )
        return sorted(current)

    async def create_post(self, payload: PostCreate) -> PostRead:
        rendered = await self._render(payload.markdown)
        post_id = new_uuid7()

        async def operation() -> PostRead:
            assets = await self._validate_content(payload, rendered)
            now = datetime.now(UTC)
            post = Post(
                id=post_id,
                slug=payload.slug,
                title=payload.title,
                summary=payload.summary,
                markdown=payload.markdown,
                category_id=payload.category_id,
                cover_asset_id=payload.cover_asset_id,
                status="public",
                revision=1,
                published_at=now,
                created_at=now,
                updated_at=now,
            )
            self._repository.add(post)
            await self._repository.flush()
            await self._repository.replace_tags(post.id, payload.tag_ids)
            await self._repository.replace_assets(post.id, assets)
            await self._repository.flush()
            return (await self._present([post]))[0]

        return await self._write("posts:create", "post", post_id, {"published": True}, operation)

    async def update_post(self, post_id: uuid.UUID, payload: PostUpdate) -> PostRead:
        rendered = await self._render(payload.markdown)

        async def operation() -> PostRead:
            post = await self._require_post(post_id, lock=True)
            require_lifecycle(is_deleted=post.deleted_at is not None, expect_deleted=False)
            require_revision(post.revision, payload.revision)
            assets = await self._validate_content(payload, rendered, post_id=post.id)
            for field in ("title", "summary", "markdown", "category_id", "cover_asset_id"):
                setattr(post, field, getattr(payload, field))
            post.revision += 1
            post.updated_at = datetime.now(UTC)
            await self._repository.replace_tags(post.id, payload.tag_ids)
            await self._repository.replace_assets(post.id, assets)
            await self._repository.flush()
            return (await self._present([post]))[0]

        return await self._write(
            "posts:update",
            "post",
            post_id,
            {"fields": ["title", "summary", "markdown", "category_id", "tag_ids", "cover_asset_id"]},
            operation,
        )

    async def update_status(self, post_id: uuid.UUID, payload: PostStatusUpdate) -> PostRead:
        async def operation() -> PostRead:
            post = await self._require_post(post_id, lock=True)
            require_lifecycle(is_deleted=post.deleted_at is not None, expect_deleted=False)
            require_revision(post.revision, payload.revision)
            post.status = payload.status.value
            post.revision += 1
            post.updated_at = datetime.now(UTC)
            await self._repository.flush()
            return (await self._present([post]))[0]

        return await self._write("posts:update", "post", post_id, {"status": payload.status.value}, operation)

    async def change_lifecycle(self, payload: PostBatch, *, action: Literal["delete", "restore"]) -> BlogBatchResult:
        expected = {target.id: target.revision for target in payload.targets}

        async def operation() -> BlogBatchResult:
            posts = await self._repository.posts_by_ids(sorted(expected), lock=True)
            if len(posts) != len(expected):
                raise AppException(status_code=404, code=ErrorCode.BLOG_NOT_FOUND, message="一个或多个文章不存在")
            now = datetime.now(UTC)
            for post in posts:
                require_revision(post.revision, expected[post.id])
                require_lifecycle(is_deleted=post.deleted_at is not None, expect_deleted=action == "restore")
            for post in posts:
                post.deleted_at = now if action == "delete" else None
                post.deleted_by_id = self._actor_id if action == "delete" else None
                post.deleted_by_type = "admin" if action == "delete" else None
                if action == "restore":
                    post.status = "hidden"
                    post.deletion_reason = None
                post.updated_at = now
                post.revision += 1
            return BlogBatchResult(completed_count=len(posts), target_ids=[post.id for post in posts])

        return await self._write(
            f"posts:{action}", "post_batch", None, {"post_ids": [str(id_) for id_ in expected]}, operation
        )

    async def change_one_lifecycle(
        self, post_id: uuid.UUID, revision: int, *, action: Literal["delete", "restore"]
    ) -> BlogBatchResult:
        return await self.change_lifecycle(
            PostBatch(targets=[PostTarget(id=post_id, revision=revision)]), action=action
        )

    async def list_taxonomy(self, kind: TaxonomyName, *, page: int, page_size: int) -> TaxonomyPage:
        async def operation() -> TaxonomyPage:
            rows, total = await self._repository.list_taxonomy(kind, page=page, page_size=page_size)
            return TaxonomyPage.create(
                items=[TaxonomyRead.model_validate(row) for row in rows], page=page, page_size=page_size, total=total
            )

        return await self._database(operation)

    async def create_taxonomy(self, kind: TaxonomyName, payload: TaxonomyCreate) -> TaxonomyRead:
        id_ = new_uuid7()

        async def operation() -> TaxonomyRead:
            model = Category if kind == "categories" else Tag
            row = model(id=id_, name=payload.name, slug=payload.slug, revision=1)
            self._repository.add(row)
            await self._repository.flush()
            return TaxonomyRead.model_validate(row)

        return await self._write(f"{kind}:create", kind, id_, {"created": True}, operation)

    async def update_taxonomy(self, kind: TaxonomyName, id_: uuid.UUID, payload: TaxonomyUpdate) -> TaxonomyRead:
        async def operation() -> TaxonomyRead:
            rows = await self._require_taxonomy(kind, [id_], lock=True)
            row = rows[0]
            require_revision(row.revision, payload.revision)
            row.name, row.slug = payload.name, payload.slug
            row.revision += 1
            row.updated_at = datetime.now(UTC)
            await self._repository.flush()
            return TaxonomyRead.model_validate(row)

        return await self._write(f"{kind}:update", kind, id_, {"fields": ["name", "slug"]}, operation)

    async def _require_taxonomy(
        self, kind: TaxonomyName, ids: list[uuid.UUID], *, lock: bool = False
    ) -> list[TaxonomyModel]:
        rows = await self._repository.taxonomy(kind, ids, lock=lock)
        if len(rows) != len(ids):
            raise AppException(status_code=404, code=ErrorCode.BLOG_NOT_FOUND, message="一个或多个分类或标签已不存在")
        return rows

    async def _impact(self, kind: TaxonomyName, ids: list[uuid.UUID]) -> TaxonomyImpact:
        rows = await self._require_taxonomy(kind, ids)
        affected = await self._repository.affected_posts(kind, ids)
        digest = confirmation_digest(
            {
                "kind": kind,
                "targets": [(str(row.id), row.revision) for row in rows],
                "posts": [(str(post.id), post.revision) for post in affected],
            }
        )
        return TaxonomyImpact(
            targets=[TaxonomyRead.model_validate(row) for row in rows],
            affected_posts=len(affected),
            confirmation=digest,
        )

    async def deletion_impact(self, kind: TaxonomyName, ids: list[uuid.UUID]) -> TaxonomyImpact:
        return await self._database(lambda: self._impact(kind, ids))

    async def delete_taxonomy(self, kind: TaxonomyName, payload: TaxonomyDelete) -> BlogBatchResult:
        async def operation() -> BlogBatchResult:
            await self._require_taxonomy(kind, payload.target_ids, lock=True)
            impact = await self._impact(kind, payload.target_ids)
            if not hmac.compare_digest(impact.confirmation, payload.confirmation):
                raise AppException(
                    status_code=412,
                    code=ErrorCode.BLOG_DELETE_IMPACT_CHANGED,
                    message="删除目标或受影响文章已变化，请取消并重新预览后确认",
                )
            affected = await self._repository.affected_posts(kind, payload.target_ids)
            now = datetime.now(UTC)
            for post in affected:
                if kind == "categories":
                    post.category_id = None
                post.revision += 1
                post.updated_at = now
            await self._repository.delete_taxonomy(kind, payload.target_ids)
            return BlogBatchResult(completed_count=len(payload.target_ids), target_ids=payload.target_ids)

        return await self._write(
            f"{kind}:delete", f"{kind}_batch", None, {"target_ids": [str(id_) for id_ in payload.target_ids]}, operation
        )
