from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from tee_concierge import __version__
from tee_concierge.application.admin import CatalogAdmin
from tee_concierge.application.ingest import IngestWebhook
from tee_concierge.config import get_settings
from tee_concierge.domain.errors import ConflictError, InvalidInputError, NotFoundError
from tee_concierge.infrastructure.persistence.admin_repository import (
    SqlAdminCatalogRepository,
    SqlUsageRepository,
)
from tee_concierge.infrastructure.persistence.catalog_repository import SqlCatalogRepository
from tee_concierge.infrastructure.persistence.database import create_engine, create_sessionmaker
from tee_concierge.infrastructure.persistence.repository import SqlMessageRepository
from tee_concierge.infrastructure.queue.arq_queue import ArqJobQueue
from tee_concierge.infrastructure.whatsapp.parser import parse_webhook
from tee_concierge.interfaces.api import admin, dev, webhook
from tee_concierge.logging import configure_logging


@asynccontextmanager
async def default_lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    sessions = create_sessionmaker(engine)
    repo = SqlMessageRepository(sessions)
    app.state.repo = repo
    app.state.catalog = SqlCatalogRepository(sessions)
    app.state.usage = SqlUsageRepository(sessions)
    app.state.catalog_admin = CatalogAdmin(SqlAdminCatalogRepository(sessions))
    app.state.ingest = IngestWebhook(repo, ArqJobQueue(pool), parse_webhook)
    try:
        yield
    finally:
        await pool.aclose()
        await engine.dispose()


def create_app(
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="Tee Concierge", version=__version__, lifespan=lifespan or default_lifespan)
    app.include_router(webhook.router)
    app.include_router(admin.router)
    app.mount("/metrics", make_asgi_app())

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(InvalidInputError)
    async def _invalid(_: Request, exc: InvalidInputError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=422)

    if settings.whatsapp_gateway == "fake":
        app.include_router(dev.router)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
