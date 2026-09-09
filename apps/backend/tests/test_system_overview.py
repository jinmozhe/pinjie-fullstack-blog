import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from redis.exceptions import RedisError

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.domains.admin.schemas import SystemTelemetryRead
from app.services.admin_management import AdminManagementService


def _settings(*, redis_mode: str = "required") -> Settings:
    return Settings.model_construct(
        project_name="Pinjie",
        environment="test",
        dependency_timeout=2.0,
        redis_mode=redis_mode,
        security_event_retention_days=180,
        upload_storage_driver="local",
        upload_base_url="/static/uploads",
        release_version="test-release",
        web_origins=["http://127.0.0.1:3100"],
        admin_origins=["http://127.0.0.1:3101"],
    )


def _service(
    *,
    session: AsyncMock | None = None,
    redis: AsyncMock | None = None,
    redis_mode: str = "required",
) -> AdminManagementService:
    database_session = session or AsyncMock()
    resources = SimpleNamespace(engine=object(), redis=redis)
    return AdminManagementService(
        session=database_session,
        session_factory=AsyncMock(),
        settings=_settings(redis_mode=redis_mode),
        password_manager=AsyncMock(),
        metadata=AsyncMock(),
        actor_id=uuid.uuid7(),
        resources=resources,
        started_at=datetime(2026, 8, 27, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_system_telemetry_cache_hit_overrides_cache_metadata() -> None:
    sampled_at = datetime(2026, 8, 27, 8, 0, tzinfo=UTC)
    redis = AsyncMock()
    redis.get.return_value = json.dumps(
        {
            "status": "ok",
            "sampled_at": sampled_at.isoformat(),
            "user_count": 7,
            "admin_count": 2,
            "role_count": 3,
            "asset_count": 11,
            "audit_event_count": 13,
        }
    )
    service = _service(redis=redis)

    telemetry = await service._read_system_telemetry_cache(service.cache_keys.system_telemetry())

    assert telemetry is not None
    assert telemetry.cached is True
    assert telemetry.source == "redis_cache"
    assert telemetry.sampled_at == sampled_at


@pytest.mark.asyncio
async def test_system_telemetry_query_uses_current_entity_scopes() -> None:
    session = AsyncMock()
    session.execute.return_value = SimpleNamespace(one=lambda: (7, 2, 3, 11, 13))
    service = _service(session=session)

    telemetry = await service._query_system_telemetry(datetime(2026, 8, 27, 8, 0, tzinfo=UTC))

    assert telemetry.status == "ok"
    assert telemetry.source == "database"
    statement = str(session.execute.await_args.args[0])
    assert "users.deleted_at IS NULL" in statement
    assert "admins.is_active IS true" in statement
    assert "roles.is_active IS true" in statement
    assert "audit_events.occurred_at >=" in statement


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [TimeoutError(), RuntimeError("database offline")])
async def test_system_telemetry_query_reports_dependency_failures(error: Exception) -> None:
    session = AsyncMock()
    session.execute.side_effect = error
    service = _service(session=session)

    telemetry = await service._query_system_telemetry(datetime(2026, 8, 27, 8, 0, tzinfo=UTC))

    assert telemetry.status == "unavailable"
    assert telemetry.source == "unavailable"
    assert telemetry.user_count is None


@pytest.mark.asyncio
async def test_system_telemetry_cache_failures_fall_back_without_hiding_errors() -> None:
    redis = AsyncMock()
    redis.get.side_effect = [None, RedisError("read failed")]
    service = _service(redis=redis)
    cache_key = service.cache_keys.system_telemetry()

    assert await service._read_system_telemetry_cache(cache_key) is None
    assert await service._read_system_telemetry_cache(cache_key) is None

    telemetry = SystemTelemetryRead(
        status="ok",
        sampled_at=datetime(2026, 8, 27, 8, 0, tzinfo=UTC),
        source="database",
        user_count=7,
        admin_count=2,
        role_count=3,
        asset_count=11,
        audit_event_count=13,
        cached=False,
    )
    redis.setex.side_effect = RedisError("write failed")
    await service._write_system_telemetry_cache(cache_key, telemetry)
    redis.setex.assert_awaited_once()


@pytest.mark.asyncio
async def test_system_telemetry_load_rechecks_cache_inside_refresh_lock() -> None:
    sampled_at = datetime(2026, 8, 27, 8, 0, tzinfo=UTC)
    cached = SystemTelemetryRead(
        status="ok",
        sampled_at=sampled_at,
        source="redis_cache",
        user_count=7,
        admin_count=2,
        role_count=3,
        asset_count=11,
        audit_event_count=13,
        cached=True,
    )
    service = _service(redis=AsyncMock())
    service._read_system_telemetry_cache = AsyncMock(side_effect=[None, cached])
    service._query_system_telemetry = AsyncMock()

    result = await service._load_system_telemetry(redis_available=True, sampled_at=sampled_at)

    assert result == cached
    assert service._read_system_telemetry_cache.await_count == 2
    service._query_system_telemetry.assert_not_awaited()


@pytest.mark.asyncio
async def test_system_telemetry_load_returns_first_cache_hit() -> None:
    sampled_at = datetime(2026, 8, 27, 8, 0, tzinfo=UTC)
    cached = SystemTelemetryRead(
        status="ok",
        sampled_at=sampled_at,
        source="redis_cache",
        user_count=7,
        admin_count=2,
        role_count=3,
        asset_count=11,
        audit_event_count=13,
        cached=True,
    )
    service = _service(redis=AsyncMock())
    service._read_system_telemetry_cache = AsyncMock(return_value=cached)

    result = await service._load_system_telemetry(redis_available=True, sampled_at=sampled_at)

    assert result == cached
    service._read_system_telemetry_cache.assert_awaited_once()


@pytest.mark.asyncio
async def test_system_telemetry_load_without_redis_queries_database_directly() -> None:
    sampled_at = datetime(2026, 8, 27, 8, 0, tzinfo=UTC)
    telemetry = SystemTelemetryRead(
        status="ok",
        sampled_at=sampled_at,
        source="database",
        user_count=7,
        admin_count=2,
        role_count=3,
        asset_count=11,
        audit_event_count=13,
        cached=False,
    )
    service = _service(redis=None, redis_mode="disabled")
    service._read_system_telemetry_cache = AsyncMock()
    service._query_system_telemetry = AsyncMock(return_value=telemetry)
    service._write_system_telemetry_cache = AsyncMock()

    result = await service._load_system_telemetry(redis_available=False, sampled_at=sampled_at)

    assert result == telemetry
    service._read_system_telemetry_cache.assert_not_awaited()
    service._query_system_telemetry.assert_awaited_once_with(sampled_at)
    service._write_system_telemetry_cache.assert_not_awaited()


@pytest.mark.asyncio
async def test_required_redis_failure_marks_overview_unavailable() -> None:
    service = _service(redis=AsyncMock())
    service._load_system_telemetry = AsyncMock(
        return_value=SystemTelemetryRead(
            status="ok",
            sampled_at=datetime(2026, 8, 27, 8, 0, tzinfo=UTC),
            source="database",
            user_count=7,
            admin_count=2,
            role_count=3,
            asset_count=11,
            audit_event_count=13,
            cached=False,
        )
    )

    with (
        patch("app.services.admin_management.check_database", new=AsyncMock(return_value=(True, "ok"))),
        patch("app.services.admin_management.check_redis", new=AsyncMock(return_value=False)),
    ):
        overview = await service.get_system_overview()

    assert overview.status == "unavailable"
    assert overview.infrastructure.redis.status == "unavailable"


@pytest.mark.asyncio
async def test_disabled_redis_and_failed_telemetry_mark_overview_degraded() -> None:
    service = _service(redis=None, redis_mode="disabled")
    service._load_system_telemetry = AsyncMock(
        return_value=SystemTelemetryRead(
            status="unavailable",
            sampled_at=datetime(2026, 8, 27, 8, 0, tzinfo=UTC),
            source="unavailable",
            user_count=None,
            admin_count=None,
            role_count=None,
            asset_count=None,
            audit_event_count=None,
            cached=False,
        )
    )

    with patch("app.services.admin_management.check_database", new=AsyncMock(return_value=(True, "ok"))):
        overview = await service.get_system_overview()

    assert overview.status == "degraded"
    assert overview.infrastructure.redis.status == "disabled"
    assert overview.release_version == "test-release"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("database_state", "expected_status"),
    [("migration_revision_mismatch", "mismatch"), ("timeout", "timeout")],
)
async def test_database_probe_failures_skip_business_telemetry(
    database_state: str,
    expected_status: str,
) -> None:
    service = _service(redis=AsyncMock())
    service._load_system_telemetry = AsyncMock()

    with (
        patch("app.services.admin_management.check_database", new=AsyncMock(return_value=(False, database_state))),
        patch("app.services.admin_management.check_redis", new=AsyncMock(return_value=True)),
    ):
        overview = await service.get_system_overview()

    assert overview.status == "unavailable"
    assert overview.infrastructure.database.status == expected_status
    assert overview.telemetry.status == "unavailable"
    service._load_system_telemetry.assert_not_awaited()


@pytest.mark.asyncio
async def test_system_overview_without_initialized_resources_is_unavailable() -> None:
    service = _service()
    service.resources = None
    service._load_system_telemetry = AsyncMock()

    assert await service._read_system_telemetry_cache("system-telemetry") is None
    await service._write_system_telemetry_cache(
        "system-telemetry",
        SystemTelemetryRead(
            status="unavailable",
            sampled_at=datetime(2026, 8, 27, 8, 0, tzinfo=UTC),
            source="unavailable",
            user_count=None,
            admin_count=None,
            role_count=None,
            asset_count=None,
            audit_event_count=None,
            cached=False,
        ),
    )

    overview = await service.get_system_overview()

    assert overview.status == "unavailable"
    assert overview.infrastructure.database.details == "database_check_failed"
    assert overview.infrastructure.redis.status == "disabled"
    service._load_system_telemetry.assert_not_awaited()


@pytest.mark.asyncio
async def test_request_logs_fail_closed_when_metadata_logging_is_disabled() -> None:
    service = _service()

    with pytest.raises(AppException) as error:
        await service.list_request_logs(page=1, page_size=20)

    assert error.value.status_code == 409
    assert error.value.code == ErrorCode.STATE_CONFLICT
