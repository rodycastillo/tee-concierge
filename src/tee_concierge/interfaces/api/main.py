from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from tee_concierge import __version__
from tee_concierge.application.ingest import IngestWebhook
from tee_concierge.config import get_settings
from tee_concierge.infrastructure.persistence.database import create_engine, create_sessionmaker
from tee_concierge.infrastructure.persistence.repository import SqlMessageRepository
from tee_concierge.infrastructure.queue.arq_queue import ArqJobQueue
from tee_concierge.infrastructure.whatsapp.parser import parse_inbound_messages
from tee_concierge.interfaces.api import dev, webhook
from tee_concierge.logging import configure_logging


@asynccontextmanager
async def default_lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    repo = SqlMessageRepository(create_sessionmaker(engine))
    app.state.repo = repo
    app.state.ingest = IngestWebhook(repo, ArqJobQueue(pool), parse_inbound_messages)
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
    if settings.whatsapp_gateway == "fake":
        app.include_router(dev.router)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
