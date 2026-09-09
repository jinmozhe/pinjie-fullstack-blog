from datetime import UTC, datetime

import pytest
from jwt import InvalidTokenError

from app.core.cache_keys import CacheKeys
from app.core.security import PasswordManager, create_access_token, decode_access_token, new_opaque_token, token_digest
from app.domains.admin.permissions import (
    PERMISSION_CATALOG,
    PERMISSION_CODES,
    ROLE_ASSIGNABLE_PERMISSION_CODES,
    PermissionCode,
)


def test_access_token_requires_audience_and_complete_claims() -> None:
    subject = __import__("uuid").uuid7()
    session = __import__("uuid").uuid7()
    token, expires_at = create_access_token(
        subject_id=subject,
        session_id=session,
        credential_version=3,
        audience="pinjie-web",
        issuer="test-issuer",
        secret="a" * 32,
        ttl_seconds=900,
        now=datetime.now(UTC),
    )
    claims = decode_access_token(token, audience="pinjie-web", issuer="test-issuer", secret="a" * 32)
    assert claims.subject_id == subject
    assert claims.session_id == session
    assert claims.credential_version == 3
    assert claims.expires_at == expires_at.replace(microsecond=0)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, audience="pinjie-admin", issuer="test-issuer", secret="a" * 32)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, audience="pinjie-web", issuer="test-issuer", secret="b" * 32)


def test_opaque_tokens_and_cache_keys_do_not_expose_identifiers() -> None:
    token = new_opaque_token()
    digest = token_digest(token, "h" * 32)
    assert len(token) >= 64
    assert len(digest) == 64
    assert token not in digest
    keys = CacheKeys(project="pinjie", environment="test")
    key = keys.login_identifier(digest)
    assert key == f"pinjie:test:auth-web:login-id:v1:{digest}"
    assert keys.system_telemetry() == "pinjie:test:system:telemetry:v1:overview"
    assert token not in key


@pytest.mark.asyncio
async def test_argon2id_password_hashing() -> None:
    manager = PasswordManager(max_concurrency=1)
    password_hash = await manager.hash("a sufficiently long password")
    assert password_hash.startswith("$argon2id$")
    assert await manager.verify("a sufficiently long password", password_hash)
    assert not await manager.verify("wrong password", password_hash)


def test_permission_enum_and_catalog_cannot_drift() -> None:
    assert {item.value for item in PermissionCode} == PERMISSION_CODES
    assert {item.code for item in PERMISSION_CATALOG} == PERMISSION_CODES
    assert len(PERMISSION_CODES) == len(PERMISSION_CATALOG)
    assert PermissionCode.ADMINS_UPDATE in ROLE_ASSIGNABLE_PERMISSION_CODES
    assert PermissionCode.ADMINS_SUPERUSER_CHANGE not in ROLE_ASSIGNABLE_PERMISSION_CODES
