from unittest.mock import AsyncMock

import pytest

from app.db.transaction import transaction_scope


@pytest.mark.asyncio
async def test_outer_transaction_commits() -> None:
    session = AsyncMock()
    async with transaction_scope(session):
        pass
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_outer_transaction_rolls_back_and_preserves_error() -> None:
    session = AsyncMock()
    with pytest.raises(RuntimeError, match="boom"):
        async with transaction_scope(session):
            raise RuntimeError("boom")
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_nested_transaction_for_same_session_fails_explicitly() -> None:
    session = AsyncMock()
    with pytest.raises(RuntimeError, match="same session"):
        async with transaction_scope(session):
            async with transaction_scope(session):
                pass
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_nested_transaction_for_different_sessions_owns_each_transaction() -> None:
    outer_session = AsyncMock()
    inner_session = AsyncMock()
    async with transaction_scope(outer_session):
        async with transaction_scope(inner_session):
            pass
    outer_session.commit.assert_awaited_once()
    outer_session.rollback.assert_not_awaited()
    inner_session.commit.assert_awaited_once()
    inner_session.rollback.assert_not_awaited()
