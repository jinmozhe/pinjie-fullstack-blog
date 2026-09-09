import os
import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.core.identifiers import new_uuid7
from app.db.models import Admin, Permission, SystemSetting
from app.db.transaction import transaction_scope
from app.domains.admin.permissions import CATALOG_VERSION, PERMISSION_CATALOG
from app.main import create_app
from tests.conftest import TEST_SECRETS

WEB_ORIGIN = "http://127.0.0.1:3100"
ADMIN_ORIGIN = "http://127.0.0.1:3101"
WEB_PASSWORD = "coverage-user-password"
WEB_NEW_PASSWORD = "coverage-user-new-password"
ADMIN_PASSWORD = "coverage-admin-password"
ADMIN_NEW_PASSWORD = "coverage-admin-new-password"


def _settings() -> Settings:
    database_url = os.getenv("TEST_DATABASE_URL")
    redis_url = os.getenv("TEST_REDIS_URL")
    if not database_url:
        pytest.fail("TEST_DATABASE_URL is required for coverage integration tests")
    if not redis_url:
        pytest.fail("TEST_REDIS_URL is required for coverage integration tests")
    return Settings(
        ENVIRONMENT="test",
        DATABASE_URL=database_url,
        TEST_DATABASE_URL=database_url,
        REDIS_MODE="required",
        REDIS_URL=redis_url,
        REQUEST_LOG_MODE="metadata",
        **{key: value for key, value in TEST_SECRETS.items() if key not in {"REDIS_MODE", "REDIS_URL"}},
    )


@pytest.fixture
async def coverage_app() -> AsyncIterator[FastAPI]:
    test_app = create_app(_settings())
    async with test_app.router.lifespan_context(test_app):
        resources = test_app.state.resources
        assert resources.redis is not None
        await resources.redis.flushdb()
        async with resources.session_factory() as session, transaction_scope(session):
            registration = await session.scalar(
                select(SystemSetting).where(SystemSetting.setting_group == "registration").with_for_update()
            )
            assert registration is not None
            registration.setting_value = {"enabled": True}
            registration.revision += 1
        yield test_app
        await resources.redis.flushdb()


def _client(test_app: FastAPI) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=test_app, raise_app_exceptions=False, client=("127.0.0.1", 43127)),
        base_url="http://testserver",
    )


def _csrf_headers(client: AsyncClient, *, admin: bool = False) -> dict[str, str]:
    cookie_name = "pinjie_blog_admin_csrf" if admin else "pinjie_blog_web_csrf"
    token = client.cookies.get(cookie_name)
    assert token
    return {
        "Origin": ADMIN_ORIGIN if admin else WEB_ORIGIN,
        "X-CSRF-Token": token,
    }


async def _seed_superuser(test_app: FastAPI, username: str) -> uuid.UUID:
    resources = test_app.state.resources
    password_hash = await resources.password_manager.hash(ADMIN_PASSWORD)
    admin_id = new_uuid7()
    async with resources.session_factory() as session, transaction_scope(session):
        existing_codes = set((await session.scalars(select(Permission.code))).all())
        for item in PERMISSION_CATALOG:
            if item.code not in existing_codes:
                session.add(
                    Permission(
                        id=new_uuid7(),
                        code=item.code,
                        name=item.name,
                        description=item.description,
                        is_active=True,
                        catalog_version=CATALOG_VERSION,
                    )
                )
        session.add(
            Admin(
                id=admin_id,
                username=username,
                display_name="Coverage Superuser",
                password_hash=password_hash,
                is_active=True,
                is_superuser=True,
                credential_version=1,
            )
        )
    return admin_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_browser_api_complete_account_lifecycle(coverage_app: FastAPI) -> None:
    suffix = uuid.uuid7().hex[:12]
    username = f"coverage-user-{suffix}"
    other_username = f"coverage-other-{suffix}"
    email = f"coverage-{suffix}@example.test"
    other_email = f"coverage-other-{suffix}@example.test"

    async with _client(coverage_app) as client, _client(coverage_app) as second_client:
        missing = await client.get("/api/v1/users/me")
        assert missing.status_code == 401

        response = await client.post(
            "/api/v1/auth/register",
            headers={"Origin": WEB_ORIGIN},
            json={"username": username, "password": WEB_PASSWORD, "display_name": " Coverage User ", "email": email},
        )
        assert response.status_code == 201, response.text
        user_id = response.json()["data"]["principal"]["id"]
        first_session_id = response.json()["data"]["session_id"]

        duplicate = await second_client.post(
            "/api/v1/auth/register",
            headers={"Origin": WEB_ORIGIN},
            json={"username": username, "password": WEB_PASSWORD},
        )
        assert duplicate.status_code == 409

        unknown_login = await second_client.post(
            "/api/v1/auth/login",
            headers={"Origin": WEB_ORIGIN},
            json={"username": f"missing-{suffix}", "password": WEB_PASSWORD},
        )
        assert unknown_login.status_code == 401
        wrong_login = await second_client.post(
            "/api/v1/auth/login",
            headers={"Origin": WEB_ORIGIN},
            json={"username": username, "password": "wrong-password"},
        )
        assert wrong_login.status_code == 401
        good_login = await second_client.post(
            "/api/v1/auth/login",
            headers={"Origin": WEB_ORIGIN},
            json={"username": username, "password": WEB_PASSWORD},
        )
        assert good_login.status_code == 200, good_login.text

        current = await client.get("/api/v1/users/me")
        assert current.status_code == 200
        assert current.json()["data"]["id"] == user_id

        invalid_update = await client.patch(
            "/api/v1/users/me",
            headers=_csrf_headers(client),
            json={},
        )
        assert invalid_update.status_code == 422
        updated = await client.patch(
            "/api/v1/users/me",
            headers=_csrf_headers(client),
            json={"display_name": " Updated User ", "email": email.upper()},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["data"]["display_name"] == "Updated User"
        assert updated.json()["data"]["email"] == email

        registered_other = await second_client.post(
            "/api/v1/auth/register",
            headers={"Origin": WEB_ORIGIN},
            json={"username": other_username, "password": WEB_PASSWORD, "email": other_email},
        )
        assert registered_other.status_code == 201
        conflict = await client.patch(
            "/api/v1/users/me",
            headers=_csrf_headers(client),
            json={"email": other_email},
        )
        assert conflict.status_code == 409

        sessions = await client.get("/api/v1/users/me/sessions")
        assert sessions.status_code == 200
        session_items = sessions.json()["data"]["items"]
        assert len(session_items) >= 2
        other_session_id = next(item["id"] for item in session_items if not item["is_current"])

        unknown_revoke = await client.delete(f"/api/v1/users/me/sessions/{uuid.uuid7()}", headers=_csrf_headers(client))
        assert unknown_revoke.status_code == 404
        revoked = await client.delete(f"/api/v1/users/me/sessions/{other_session_id}", headers=_csrf_headers(client))
        assert revoked.status_code == 200
        revoke_others = await client.post("/api/v1/users/me/sessions/revoke-others", headers=_csrf_headers(client))
        assert revoke_others.status_code == 200

        wrong_password = await client.post(
            "/api/v1/users/me/password",
            headers=_csrf_headers(client),
            json={"current_password": "wrong-password", "new_password": WEB_NEW_PASSWORD},
        )
        assert wrong_password.status_code == 401
        changed = await client.post(
            "/api/v1/users/me/password",
            headers=_csrf_headers(client),
            json={"current_password": WEB_PASSWORD, "new_password": WEB_NEW_PASSWORD},
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["data"]["session_id"] == first_session_id

        refreshed = await client.post("/api/v1/auth/refresh", headers=_csrf_headers(client))
        assert refreshed.status_code == 200, refreshed.text
        logged_out = await client.post("/api/v1/auth/logout", headers=_csrf_headers(client))
        assert logged_out.status_code == 200, logged_out.text
        assert (await client.get("/api/v1/users/me")).status_code == 401

        logged_in_again = await client.post(
            "/api/v1/auth/login",
            headers={"Origin": WEB_ORIGIN},
            json={"username": username, "password": WEB_NEW_PASSWORD},
        )
        assert logged_in_again.status_code == 200
        wrong_delete = await client.request(
            "DELETE",
            "/api/v1/users/me",
            headers=_csrf_headers(client),
            json={"current_password": "wrong-password"},
        )
        assert wrong_delete.status_code == 401
        deleted = await client.request(
            "DELETE",
            "/api/v1/users/me",
            headers=_csrf_headers(client),
            json={"current_password": WEB_NEW_PASSWORD},
        )
        assert deleted.status_code == 200, deleted.text
        assert (await client.get("/api/v1/users/me")).status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_browser_api_complete_management_lifecycle(coverage_app: FastAPI) -> None:
    suffix = uuid.uuid7().hex[:12]
    root_username = f"coverage-root-{suffix}"
    target_username = f"coverage-admin-{suffix}"
    role_code = f"coverage_role_{suffix}"
    managed_username = f"managed-user-{suffix}"
    await _seed_superuser(coverage_app, root_username)

    async with (
        _client(coverage_app) as admin_client,
        _client(coverage_app) as target_client,
        _client(coverage_app) as managed_client,
    ):
        registered = await managed_client.post(
            "/api/v1/auth/register",
            headers={"Origin": WEB_ORIGIN},
            json={"username": managed_username, "password": WEB_PASSWORD, "display_name": "Managed User"},
        )
        assert registered.status_code == 201
        managed_user_id = registered.json()["data"]["principal"]["id"]
        managed_session_id = registered.json()["data"]["session_id"]

        missing_admin = await admin_client.get("/api/v1/admin/auth/me")
        assert missing_admin.status_code == 401
        unknown_login = await admin_client.post(
            "/api/v1/admin/auth/login",
            headers={"Origin": ADMIN_ORIGIN},
            json={"username": f"missing-{suffix}", "password": ADMIN_PASSWORD},
        )
        assert unknown_login.status_code == 401
        wrong_login = await admin_client.post(
            "/api/v1/admin/auth/login",
            headers={"Origin": ADMIN_ORIGIN},
            json={"username": root_username, "password": "wrong-password"},
        )
        assert wrong_login.status_code == 401
        logged_in = await admin_client.post(
            "/api/v1/admin/auth/login",
            headers={"Origin": ADMIN_ORIGIN},
            json={"username": root_username, "password": ADMIN_PASSWORD},
        )
        assert logged_in.status_code == 200, logged_in.text
        root_id = logged_in.json()["data"]["principal"]["id"]
        assert (await admin_client.get("/api/v1/admin/auth/me")).status_code == 200

        invalid_profile = await admin_client.patch(
            "/api/v1/admin/auth/profile",
            headers=_csrf_headers(admin_client, admin=True),
            json={},
        )
        assert invalid_profile.status_code == 422
        updated_profile = await admin_client.patch(
            "/api/v1/admin/auth/profile",
            headers=_csrf_headers(admin_client, admin=True),
            json={"display_name": "Root New Display", "avatar": "https://example.com/avatar.png"},
        )
        assert updated_profile.status_code == 200
        assert updated_profile.json()["data"]["display_name"] == "Root New Display"
        assert updated_profile.json()["data"]["avatar"] == "https://example.com/avatar.png"

        refreshed = await admin_client.post(
            "/api/v1/admin/auth/refresh", headers=_csrf_headers(admin_client, admin=True)
        )
        assert refreshed.status_code == 200, refreshed.text
        permissions = await admin_client.get("/api/v1/admin/permissions")
        assert permissions.status_code == 200, permissions.text
        assert len(permissions.json()["data"]) == len(PERMISSION_CATALOG)

        role = await admin_client.post(
            "/api/v1/admin/roles",
            headers=_csrf_headers(admin_client, admin=True),
            json={"code": role_code, "name": " Coverage Role ", "description": " role description "},
        )
        assert role.status_code == 201, role.text
        role_id = role.json()["data"]["id"]
        duplicate_role = await admin_client.post(
            "/api/v1/admin/roles",
            headers=_csrf_headers(admin_client, admin=True),
            json={"code": role_code, "name": "Duplicate"},
        )
        assert duplicate_role.status_code == 409
        assert (await admin_client.get("/api/v1/admin/roles")).status_code == 200
        assert (await admin_client.get(f"/api/v1/admin/roles/{role_id}")).status_code == 200
        updated_role = await admin_client.patch(
            f"/api/v1/admin/roles/{role_id}",
            headers=_csrf_headers(admin_client, admin=True),
            json={"name": "Updated Coverage Role", "description": None},
        )
        assert updated_role.status_code == 200

        assigned_permissions = await admin_client.put(
            f"/api/v1/admin/roles/{role_id}/permissions",
            headers=_csrf_headers(admin_client, admin=True),
            json={
                "permission_codes": [
                    "users:read",
                    "roles:read",
                    "admins:create",
                    "admins:update",
                    "admins:credentials:reset",
                    "admins:roles:assign",
                    "admins:sessions:read",
                    "admins:sessions:revoke",
                ]
            },
        )
        assert assigned_permissions.status_code == 200, assigned_permissions.text
        system_permission_rejected = await admin_client.put(
            f"/api/v1/admin/roles/{role_id}/permissions",
            headers=_csrf_headers(admin_client, admin=True),
            json={"permission_codes": ["admins:superuser:change"]},
        )
        assert system_permission_rejected.status_code == 422

        created_admin = await admin_client.post(
            "/api/v1/admin/admins",
            headers=_csrf_headers(admin_client, admin=True),
            json={
                "username": target_username,
                "initial_password": ADMIN_PASSWORD,
                "display_name": "Coverage Administrator",
                "role_ids": [role_id],
            },
        )
        assert created_admin.status_code == 201, created_admin.text
        target_id = created_admin.json()["data"]["id"]
        duplicate_admin = await admin_client.post(
            "/api/v1/admin/admins",
            headers=_csrf_headers(admin_client, admin=True),
            json={"username": target_username, "initial_password": ADMIN_PASSWORD},
        )
        assert duplicate_admin.status_code == 409

        target_login = await target_client.post(
            "/api/v1/admin/auth/login",
            headers={"Origin": ADMIN_ORIGIN},
            json={"username": target_username, "password": ADMIN_PASSWORD},
        )
        assert target_login.status_code == 200, target_login.text
        forbidden_superuser_create = await target_client.post(
            "/api/v1/admin/admins",
            headers=_csrf_headers(target_client, admin=True),
            json={
                "username": f"forbidden-superuser-{suffix}",
                "initial_password": ADMIN_PASSWORD,
                "is_superuser": True,
            },
        )
        assert forbidden_superuser_create.status_code == 403
        protected_superuser_requests = [
            await target_client.patch(
                f"/api/v1/admin/admins/{root_id}",
                headers=_csrf_headers(target_client, admin=True),
                json={"display_name": "Forbidden Root Update"},
            ),
            await target_client.patch(
                f"/api/v1/admin/admins/{root_id}/status",
                headers=_csrf_headers(target_client, admin=True),
                json={"is_active": False},
            ),
            await target_client.patch(
                "/api/v1/admin/admins/status/batch",
                headers=_csrf_headers(target_client, admin=True),
                json={"admin_ids": [root_id], "is_active": False},
            ),
            await target_client.put(
                f"/api/v1/admin/admins/{root_id}/credentials/password",
                headers=_csrf_headers(target_client, admin=True),
                json={"new_password": ADMIN_NEW_PASSWORD},
            ),
            await target_client.put(
                f"/api/v1/admin/admins/{root_id}/roles",
                headers=_csrf_headers(target_client, admin=True),
                json={"role_ids": [role_id]},
            ),
            await target_client.get(f"/api/v1/admin/admins/{root_id}/sessions"),
            await target_client.post(
                f"/api/v1/admin/admins/{root_id}/sessions/revoke-all",
                headers=_csrf_headers(target_client, admin=True),
            ),
        ]
        assert all(response.status_code == 403 for response in protected_superuser_requests)
        assert (await admin_client.get("/api/v1/admin/admins")).status_code == 200
        assert (await admin_client.get(f"/api/v1/admin/admins/{target_id}")).status_code == 200
        assert (await admin_client.get(f"/api/v1/admin/admins/{target_id}/sessions")).status_code == 200

        updated_admin = await admin_client.patch(
            f"/api/v1/admin/admins/{target_id}",
            headers=_csrf_headers(admin_client, admin=True),
            json={"display_name": " Updated Administrator "},
        )
        assert updated_admin.status_code == 200
        legacy_superuser_change = await admin_client.patch(
            f"/api/v1/admin/admins/{target_id}",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_superuser": True},
        )
        assert legacy_superuser_change.status_code == 422
        promoted = await admin_client.patch(
            f"/api/v1/admin/admins/{target_id}/superuser",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_superuser": True},
        )
        assert promoted.status_code == 200
        demoted = await admin_client.patch(
            f"/api/v1/admin/admins/{target_id}/superuser",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_superuser": False},
        )
        assert demoted.status_code == 200

        own_superuser_change = await admin_client.patch(
            f"/api/v1/admin/admins/{root_id}/superuser",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_superuser": False},
        )
        assert own_superuser_change.status_code == 409

        disabled_admin = await admin_client.patch(
            f"/api/v1/admin/admins/{target_id}/status",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_active": False},
        )
        assert disabled_admin.status_code == 200
        enabled_admin = await admin_client.patch(
            f"/api/v1/admin/admins/{target_id}/status",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_active": True},
        )
        assert enabled_admin.status_code == 200

        assigned_roles = await admin_client.put(
            f"/api/v1/admin/admins/{target_id}/roles",
            headers=_csrf_headers(admin_client, admin=True),
            json={"role_ids": [role_id]},
        )
        assert assigned_roles.status_code == 200
        reset_password = await admin_client.put(
            f"/api/v1/admin/admins/{target_id}/credentials/password",
            headers=_csrf_headers(admin_client, admin=True),
            json={"new_password": ADMIN_NEW_PASSWORD},
        )
        assert reset_password.status_code == 200

        target_relogin = await target_client.post(
            "/api/v1/admin/auth/login",
            headers={"Origin": ADMIN_ORIGIN},
            json={"username": target_username, "password": ADMIN_NEW_PASSWORD},
        )
        assert target_relogin.status_code == 200
        revoked_admin_sessions = await admin_client.post(
            f"/api/v1/admin/admins/{target_id}/sessions/revoke-all",
            headers=_csrf_headers(admin_client, admin=True),
        )
        assert revoked_admin_sessions.status_code == 200

        users = await admin_client.get(f"/api/v1/admin/users?search={managed_username}")
        assert users.status_code == 200
        assert users.json()["data"]["total"] >= 1
        assert (await admin_client.get(f"/api/v1/admin/users/{managed_user_id}")).status_code == 200
        updated_user = await admin_client.patch(
            f"/api/v1/admin/users/{managed_user_id}",
            headers=_csrf_headers(admin_client, admin=True),
            json={"display_name": "Updated Managed User"},
        )
        assert updated_user.status_code == 200
        assert (await admin_client.get(f"/api/v1/admin/users/{managed_user_id}/sessions")).status_code == 200
        revoked_user_session = await admin_client.delete(
            f"/api/v1/admin/users/{managed_user_id}/sessions/{managed_session_id}",
            headers=_csrf_headers(admin_client, admin=True),
        )
        assert revoked_user_session.status_code == 200
        revoked_user_sessions = await admin_client.post(
            f"/api/v1/admin/users/{managed_user_id}/sessions/revoke-all",
            headers=_csrf_headers(admin_client, admin=True),
        )
        assert revoked_user_sessions.status_code == 200
        reset_user_password = await admin_client.put(
            f"/api/v1/admin/users/{managed_user_id}/credentials/password",
            headers=_csrf_headers(admin_client, admin=True),
            json={"new_password": WEB_NEW_PASSWORD},
        )
        assert reset_user_password.status_code == 200
        disabled_user = await admin_client.patch(
            f"/api/v1/admin/users/{managed_user_id}/status",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_active": False},
        )
        assert disabled_user.status_code == 200
        enabled_user = await admin_client.patch(
            f"/api/v1/admin/users/{managed_user_id}/status",
            headers=_csrf_headers(admin_client, admin=True),
            json={"is_active": True},
        )
        assert enabled_user.status_code == 200

        assigned_none = await admin_client.put(
            f"/api/v1/admin/admins/{target_id}/roles",
            headers=_csrf_headers(admin_client, admin=True),
            json={"role_ids": []},
        )
        assert assigned_none.status_code == 200
        deleted_role = await admin_client.delete(
            f"/api/v1/admin/roles/{role_id}",
            headers=_csrf_headers(admin_client, admin=True),
        )
        assert deleted_role.status_code == 200, deleted_role.text

        assert (await admin_client.get("/api/v1/admin/security/login-events")).status_code == 200
        assert (await admin_client.get("/api/v1/admin/security/audit-events")).status_code == 200
        assert (await admin_client.get("/api/v1/admin/system/request-logs")).status_code == 200

        wrong_change = await admin_client.post(
            "/api/v1/admin/auth/password",
            headers=_csrf_headers(admin_client, admin=True),
            json={"current_password": "wrong-password", "new_password": ADMIN_NEW_PASSWORD},
        )
        assert wrong_change.status_code == 401
        changed = await admin_client.post(
            "/api/v1/admin/auth/password",
            headers=_csrf_headers(admin_client, admin=True),
            json={"current_password": ADMIN_PASSWORD, "new_password": ADMIN_NEW_PASSWORD},
        )
        assert changed.status_code == 200, changed.text
        logged_out = await admin_client.post(
            "/api/v1/admin/auth/logout", headers=_csrf_headers(admin_client, admin=True)
        )
        assert logged_out.status_code == 200, logged_out.text
        assert (await admin_client.get("/api/v1/admin/auth/me")).status_code == 401
