from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

_active_sessions: ContextVar[tuple[AsyncSession, ...]] = ContextVar("active_transaction_sessions", default=())


@asynccontextmanager
async def transaction_scope(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    active_sessions = _active_sessions.get()
    if any(active is session for active in active_sessions):
        raise RuntimeError("transaction_scope does not allow nested transactions for the same session")
    token = _active_sessions.set((*active_sessions, session))
    try:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
    finally:
        _active_sessions.reset(token)
