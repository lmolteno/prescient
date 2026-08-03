"""FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the app's session factory.

    Overridden at app startup (lifespan) and in tests. The bare implementation
    is never called directly.
    """
    raise RuntimeError("session factory not configured")


async def get_session(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[AsyncSession]:
    """Yield a read-oriented session."""
    async with factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
