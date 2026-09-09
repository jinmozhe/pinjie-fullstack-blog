import os

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.core.health import check_database


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgresql_test_database_is_isolated_and_ready() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    settings = Settings(
        ENVIRONMENT="test",
        DATABASE_URL=database_url,
        TEST_DATABASE_URL=database_url,
    )
    settings.validate_database_runtime()
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        ready, state = await check_database(engine, timeout=2)
        assert ready, state
    finally:
        await engine.dispose()
