from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_public_blog_service
from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.domains.blog.public_schemas import PublicPostPage, PublicPostRead
from app.main import create_app
from app.services.public_blog import PublicBlogService


@pytest.fixture
def public_app():
    app = create_app(Settings.model_construct())
    service = AsyncMock(spec=PublicBlogService)
    app.dependency_overrides[get_public_blog_service] = lambda: service
    return app, service


async def test_public_post_is_anonymous_and_excludes_management_fields(public_app):
    app, service = public_app
    now = datetime.now(UTC)
    service.get_post.return_value = PublicPostRead(
        title="公开文章",
        slug="public-post",
        summary="摘要",
        category=None,
        tags=[],
        cover_url=None,
        published_at=now,
        updated_at=now,
        html="<p>安全正文</p>",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/blog/posts/public-post")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()["data"]
    assert data["html"] == "<p>安全正文</p>"
    assert not {"markdown", "revision", "deleted_at", "status", "cover_asset_id", "id"} & data.keys()


@pytest.mark.parametrize("status,code", [(404, ErrorCode.NOT_FOUND), (503, ErrorCode.SERVICE_UNAVAILABLE)])
async def test_public_failures_keep_error_status_and_no_store(public_app, status, code):
    app, service = public_app
    service.get_post.side_effect = AppException(status_code=status, code=code, message="内容不可用")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/blog/posts/missing")
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["code"] == code
    assert "data" not in response.json()


async def test_search_passes_trimmed_query_and_validates_bounds(public_app):
    app, service = public_app
    service.list_posts.return_value = PublicPostPage.create(items=[], page=1, page_size=12, total=0)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/blog/posts", params={"q": "  100%_  "})
        assert response.status_code == 200
        assert service.list_posts.call_args.args[0].q == "100%_"
        for params in ({"page": 0}, {"page_size": 101}, {"q": "字" * 101}, {"status": "hidden"}):
            response = await client.get("/api/v1/blog/posts", params=params)
            assert response.status_code == 422
            assert response.headers["cache-control"] == "no-store"
