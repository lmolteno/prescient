"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from prescient.api.deps import get_session_factory
from prescient.api.routes import sdo, swpc
from prescient.config import Settings, get_settings
from prescient.db import create_engine, create_session_factory
from prescient.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app. Manages the DB engine over the app lifespan."""
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json=settings.log_json)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)
        app.dependency_overrides.setdefault(get_session_factory, lambda: factory)
        app.state.session_factory = factory
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(
        title="Prescient",
        version="0.1.0",
        summary="Space-weather data: SWPC solar regions/events and SDO/HMI sunspot contours.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(swpc.router)
    app.include_router(sdo.router)
    return app
