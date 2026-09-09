from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_blog_service, get_current_admin, get_db_session
from app.core.config import Settings
from app.core.cookies import ADMIN_COOKIES
from app.core.security import token_digest
from app.domains.admin.permissions import PERMISSION_CODES
from app.domains.blog.router import router
from app.domains.blog.schemas import MarkdownPreview
from app.main import create_app
from app.services.blog import BlogService

ENDPOINTS = [(method, route.path) for route in router.routes for method in route.methods]


@pytest.mark.parametrize("method,path", ENDPOINTS)
async def test_every_blog_endpoint_rejects_missing_identity_and_missing_permission(method, path):
    settings = Settings.model_construct(
        web_jwt_secret="w" * 40,
        admin_jwt_secret="a" * 40,
        web_token_hmac_key="x" * 40,
        admin_token_hmac_key="y" * 40,
        admin_origins=["http://localhost:3001"],
    )
    app = create_app(settings)
    service = AsyncMock(spec=BlogService)
    app.dependency_overrides[get_blog_service] = lambda: service
    app.dependency_overrides[get_db_session] = lambda: object()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.request(method, f"/api/v1{path}", json={})
        assert response.status_code == 401
        app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(
            permissions=frozenset(), login_session=SimpleNamespace(csrf_digest=token_digest("csrf-test", "y" * 40))
        )
        client.cookies.set(ADMIN_COOKIES.csrf, "csrf-test")
        response = await client.request(
            method,
            f"/api/v1{path}",
            json={},
            headers={"Origin": "http://localhost:3001", "X-CSRF-Token": "csrf-test"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "PERMISSION_DENIED"


async def test_preview_checks_csrf_and_returns_no_store_html_without_persisting():
    settings = Settings.model_construct(
        web_jwt_secret="w" * 40,
        admin_jwt_secret="a" * 40,
        web_token_hmac_key="x" * 40,
        admin_token_hmac_key="y" * 40,
        admin_origins=["http://localhost:3001"],
    )
    app = create_app(settings)
    service = AsyncMock(spec=BlogService)
    service.preview.return_value = MarkdownPreview(html="<p>内容</p>\n")
    app.dependency_overrides[get_blog_service] = lambda: service
    current = SimpleNamespace(
        permissions=PERMISSION_CODES, login_session=SimpleNamespace(csrf_digest=token_digest("csrf-test", "y" * 40))
    )
    app.dependency_overrides[get_current_admin] = lambda: current
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        client.cookies.set(ADMIN_COOKIES.csrf, "csrf-test")
        response = await client.post("/api/v1/admin/blog/preview", json={"markdown": "内容"})
        assert response.status_code == 403
        response = await client.post(
            "/api/v1/admin/blog/preview",
            json={"markdown": "内容"},
            headers={"Origin": "http://localhost:3001", "X-CSRF-Token": "csrf-test"},
        )
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["data"]["html"] == "<p>内容</p>\n"
        service.create_post.assert_not_awaited()
