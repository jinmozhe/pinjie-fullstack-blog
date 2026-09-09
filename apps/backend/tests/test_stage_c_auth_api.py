from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.api.dependencies import get_web_auth_service
from app.core.identifiers import new_uuid7
from app.main import app
from app.services.authentication import SessionArtifacts


class FakeWebAuthService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.user = SimpleNamespace(
            id=new_uuid7(),
            username="browser-user",
            display_name="Browser User",
            email=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.artifacts = SessionArtifacts(
            session_id=new_uuid7(),
            access_token="access-token-must-not-enter-json",
            refresh_token="refresh-token-must-not-enter-json",
            csrf_token="csrf-token",
            access_expires_at=now + timedelta(minutes=15),
            idle_expires_at=now + timedelta(days=7),
            absolute_expires_at=now + timedelta(days=30),
        )

    async def login(self, _payload):
        return self.user, self.artifacts

    async def register(self, _payload):
        return self.user, self.artifacts

    async def refresh(self, _refresh_token: str, _csrf_token: str):
        return self.artifacts

    async def logout(self, _refresh_token: str, _csrf_token: str) -> None:
        return None


@pytest.fixture
def fake_web_auth_service():
    service = FakeWebAuthService()
    app.dependency_overrides[get_web_auth_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(get_web_auth_service, None)


@pytest.mark.asyncio
async def test_login_sets_cookies_without_returning_tokens(client, fake_web_auth_service) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:3100"},
        json={"username": "browser-user", "password": "password-value"},
    )
    assert response.status_code == 200
    serialized = response.text
    assert "access-token-must-not-enter-json" not in serialized
    assert "refresh-token-must-not-enter-json" not in serialized
    assert response.json()["data"]["principal"]["username"] == "browser-user"
    assert response.cookies["pinjie_blog_web_access"] == "access-token-must-not-enter-json"
    assert response.cookies["pinjie_blog_web_refresh"] == "refresh-token-must-not-enter-json"


@pytest.mark.asyncio
async def test_login_rejects_missing_origin(client, fake_web_auth_service) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "browser-user", "password": "password-value"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_REJECTED"


@pytest.mark.asyncio
async def test_web_login_rejects_admin_origin(client, fake_web_auth_service) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:3101"},
        json={"username": "browser-user", "password": "password-value"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_REJECTED"


@pytest.mark.asyncio
async def test_web_login_requires_an_exact_origin_value(client, fake_web_auth_service) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:3100/"},
        json={"username": "browser-user", "password": "password-value"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_REJECTED"


@pytest.mark.asyncio
async def test_refresh_requires_matching_csrf_cookie_and_header(client, fake_web_auth_service) -> None:
    client.cookies.set("pinjie_blog_web_refresh", "refresh-token")
    client.cookies.set("pinjie_blog_web_csrf", "csrf-token")
    response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://127.0.0.1:3100", "X-CSRF-Token": "wrong-token"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_REJECTED"
