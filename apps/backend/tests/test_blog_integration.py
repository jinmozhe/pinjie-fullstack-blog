"""仅在明确授权的独立 PostgreSQL 测试环境运行。"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.identifiers import new_uuid7
from app.core.request_metadata import RequestMetadata
from app.db.models import Admin, Asset, AuditEvent, Category, Post, PostAsset, PostTag, Tag
from app.db.repositories.asset import AssetRepository
from app.domains.blog.public_schemas import PublicPostQuery
from app.domains.blog.schemas import (
    PostBatch,
    PostCreate,
    PostStatusUpdate,
    PostTarget,
    PostUpdate,
    TaxonomyCreate,
    TaxonomyDelete,
)
from app.services.assets import AssetService
from app.services.blog import BlogService
from app.services.public_blog import PublicBlogService
from app.services.storage import LocalStorageProvider


@pytest.fixture
async def blog_database(tmp_path):
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.fail("需要显式配置独立 TEST_DATABASE_URL")
    url = make_url(value)
    if (
        not url.database
        or not url.database.endswith("_test")
        or url.host not in {"localhost", "127.0.0.1", "::1", "postgres"}
    ):
        pytest.fail("博客集成测试只允许指定主机的独立 _test 数据库")
    engine = create_async_engine(value)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    actor = new_uuid7()
    suffix = actor.hex
    async with factory() as session:
        session.add(
            Admin(
                id=actor, username=f"blog-{suffix}", password_hash="unused-test-hash", is_active=True, is_superuser=True
            )
        )
        await session.commit()
    metadata = RequestMetadata(str(new_uuid7()), str(new_uuid7()), "127.0.0.1", "blog-test", "test")
    settings = Settings.model_construct(upload_local_root=tmp_path)

    @asynccontextmanager
    async def service():
        async with factory() as session:
            yield BlogService(
                session=session, session_factory=factory, settings=settings, metadata=metadata, actor_id=actor
            )

    try:
        yield SimpleNamespace(
            service=service,
            factory=factory,
            suffix=suffix,
            actor=actor,
            settings=settings,
            metadata=metadata,
            storage=LocalStorageProvider(tmp_path, io_concurrency=2),
        )
    finally:
        async with factory() as session:
            post_ids = select(Post.id).where(Post.slug.like(f"test-{suffix}-%"))
            await session.execute(delete(PostTag).where(PostTag.post_id.in_(post_ids)))
            await session.execute(delete(PostAsset).where(PostAsset.post_id.in_(post_ids)))
            await session.execute(delete(Post).where(Post.id.in_(post_ids)))
            for model in (Category, Tag):
                await session.execute(delete(model).where(model.slug.like(f"test-{suffix}-%")))
            await session.execute(delete(Asset).where(Asset.uploader_id == actor))
            await session.execute(delete(AuditEvent).where(AuditEvent.actor_id == actor))
            await session.execute(delete(Admin).where(Admin.id == actor))
            await session.commit()
        await engine.dispose()


@pytest.mark.integration
async def test_lifecycle_and_taxonomy_transactions_cover_recycle_bin(blog_database):
    db = blog_database
    async with db.service() as service:
        category = await service.create_taxonomy(
            "categories", TaxonomyCreate(name=f"分类{db.suffix}", slug=f"test-{db.suffix}-category")
        )
        tag = await service.create_taxonomy(
            "tags", TaxonomyCreate(name=f"标签{db.suffix}", slug=f"test-{db.suffix}-tag")
        )
        other = await service.create_taxonomy(
            "tags", TaxonomyCreate(name=f"其他{db.suffix}", slug=f"test-{db.suffix}-other")
        )
        post = await service.create_post(
            PostCreate(
                title="标题",
                slug=f"test-{db.suffix}-post",
                markdown="正文",
                category_id=category.id,
                tag_ids=[tag.id, other.id],
            )
        )
        first_published = post.published_at
        post = await service.update_status(post.id, PostStatusUpdate(revision=post.revision, status="hidden"))
        post = await service.update_post(
            post.id,
            PostUpdate(
                title="编辑后",
                markdown="新正文",
                category_id=category.id,
                tag_ids=[tag.id, other.id],
                revision=post.revision,
            ),
        )
        assert post.status == "hidden" and post.published_at == first_published
        impact = await service.deletion_impact("categories", [category.id])
        await service.change_lifecycle(
            PostBatch(targets=[PostTarget(id=post.id, revision=post.revision)]), action="delete"
        )
        with pytest.raises(AppException) as stale:
            await service.delete_taxonomy(
                "categories", TaxonomyDelete(target_ids=[category.id], confirmation=impact.confirmation)
            )
        assert stale.value.code == ErrorCode.BLOG_DELETE_IMPACT_CHANGED
        impact = await service.deletion_impact("categories", [category.id])
        assert impact.affected_posts == 1
        await service.delete_taxonomy(
            "categories", TaxonomyDelete(target_ids=[category.id], confirmation=impact.confirmation)
        )
        tag_impact = await service.deletion_impact("tags", [tag.id])
        await service.delete_taxonomy("tags", TaxonomyDelete(target_ids=[tag.id], confirmation=tag_impact.confirmation))
        deleted = await service.get_post(post.id)
        assert deleted.category is None
        assert [item.id for item in deleted.tags] == [other.id]
        await service.change_one_lifecycle(post.id, deleted.revision, action="restore")
        restored = await service.get_post(post.id)
        assert restored.status == "hidden" and restored.deleted_at is None
        assert restored.published_at == first_published and restored.markdown == "新正文"


@pytest.mark.integration
async def test_concurrent_article_edits_reject_stale_revision(blog_database):
    db = blog_database
    async with db.service() as service:
        post = await service.create_post(
            PostCreate(title="原文", slug=f"test-{db.suffix}-concurrency", markdown="正文")
        )

    async def edit(title):
        async with db.service() as service:
            return await service.update_post(post.id, PostUpdate(title=title, markdown="正文", revision=post.revision))

    results = await asyncio.gather(edit("修改一"), edit("修改二"), return_exceptions=True)
    assert sum(not isinstance(result, BaseException) for result in results) == 1
    assert any(isinstance(result, AppException) and result.status_code == 412 for result in results)


@pytest.mark.integration
async def test_hidden_and_deleted_posts_protect_images_in_single_and_batch_delete(blog_database):
    db = blog_database
    asset_id = new_uuid7()
    key = f"article/{db.suffix}.png"
    now = datetime.now(UTC)
    async with db.factory() as session:
        session.add(
            Asset(
                id=asset_id,
                uploader_type="admin",
                uploader_id=db.actor,
                storage_driver="local",
                file_key=key,
                original_name="image.png",
                mime_type="image/png",
                file_size=10,
                file_hash=db.suffix * 2,
                url=f"/static/uploads/{key}",
                scene="article",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    async with db.service() as service:
        post = await service.create_post(
            PostCreate(
                title="带图片",
                slug=f"test-{db.suffix}-image",
                markdown=f"![图片](/static/uploads/{key})",
                cover_asset_id=asset_id,
            )
        )
        post = await service.update_status(post.id, PostStatusUpdate(revision=post.revision, status="hidden"))
        for deleted in (False, True):
            if deleted:
                await service.change_one_lifecycle(post.id, post.revision, action="delete")
            async with db.factory() as session:
                assets = AssetService(
                    session=session,
                    session_factory=db.factory,
                    settings=db.settings,
                    storage=db.storage,
                    metadata=db.metadata,
                )
                with pytest.raises(AppException) as single:
                    await assets.delete(asset_id=asset_id, actor_id=db.actor)
                assert single.value.status_code == 409
                with pytest.raises(AppException):
                    await assets.delete_bulk(asset_ids=[asset_id], actor_id=db.actor)
                assert await AssetRepository(session).get(asset_id) is not None


@pytest.mark.integration
async def test_batch_revision_conflict_rolls_back_every_target(blog_database):
    db = blog_database
    async with db.service() as service:
        posts = [
            await service.create_post(PostCreate(title=f"文章{i}", slug=f"test-{db.suffix}-{i}", markdown="正文"))
            for i in range(2)
        ]
        with pytest.raises(AppException):
            await service.change_lifecycle(
                PostBatch(targets=[PostTarget(id=posts[0].id, revision=1), PostTarget(id=posts[1].id, revision=99)]),
                action="delete",
            )
        assert (await service.get_post(posts[0].id)).deleted_at is None
        assert (await service.get_post(posts[1].id)).deleted_at is None


@pytest.mark.integration
async def test_public_reading_search_taxonomy_and_lifecycle_visibility(blog_database):
    db = blog_database
    async with db.service() as service:
        category = await service.create_taxonomy(
            "categories", TaxonomyCreate(name=f"公开分类{db.suffix}", slug=f"test-{db.suffix}-public")
        )
        tag = await service.create_taxonomy(
            "tags", TaxonomyCreate(name=f"公开标签{db.suffix}", slug=f"test-{db.suffix}-tag")
        )
        post = await service.create_post(
            PostCreate(
                title="Literal 100%_",
                summary="FastAPI 摘要",
                markdown="# 正文\n\n正文独有关键词",
                slug=f"test-{db.suffix}-public-post",
                category_id=category.id,
                tag_ids=[tag.id],
            )
        )
        decoy = await service.create_post(
            PostCreate(
                title="Literal 100xy", markdown="其他正文", slug=f"test-{db.suffix}-decoy", category_id=category.id
            )
        )
    async with db.factory() as session:
        reader = PublicBlogService(session=session, settings=db.settings)
        result = await reader.list_posts(PublicPostQuery(q="100%_", category=category.slug))
        assert [item.slug for item in result.items] == [post.slug]
        assert (await reader.list_posts(PublicPostQuery(q="fastapi", category=category.slug))).total == 1
        assert (await reader.list_posts(PublicPostQuery(q="正文独有关键词", category=category.slug))).total == 0
        assert (await reader.get_taxonomy("categories", category.slug)).post_count == 2
        assert (await reader.get_taxonomy("tags", tag.slug)).post_count == 1
        assert "正文独有关键词" in (await reader.get_post(post.slug)).html
        paged = await reader.list_posts(PublicPostQuery(category=category.slug, page_size=1, page=2))
        assert paged.total == 2 and len(paged.items) == 1
    async with db.service() as service:
        await service.update_status(post.id, PostStatusUpdate(revision=post.revision, status="hidden"))
        await service.change_lifecycle(
            PostBatch(targets=[PostTarget(id=decoy.id, revision=decoy.revision)]), action="delete"
        )
    async with db.factory() as session:
        reader = PublicBlogService(session=session, settings=db.settings)
        assert (await reader.list_posts(PublicPostQuery(category=category.slug))).total == 0
        for slug in (post.slug, decoy.slug, "missing-post"):
            with pytest.raises(AppException) as error:
                await reader.get_post(slug)
            assert error.value.status_code == 404
        for kind, slug in (("categories", category.slug), ("tags", tag.slug)):
            with pytest.raises(AppException) as error:
                await reader.get_taxonomy(kind, slug)
            assert error.value.status_code == 404
