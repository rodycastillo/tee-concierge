from typing import Any

import httpx
import structlog
from arq import Retry
from arq.connections import RedisSettings
from prometheus_client import start_http_server
from redis.asyncio import Redis

from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.engine import MenuEngine
from tee_concierge.application.process import ProcessInboundMessage, ProcessOutcome
from tee_concierge.config import Settings, get_settings
from tee_concierge.domain.ports import MessageGateway
from tee_concierge.infrastructure import metrics
from tee_concierge.infrastructure.persistence.admin_repository import SqlUsageRepository
from tee_concierge.infrastructure.persistence.catalog_repository import (
    SqlCatalogRepository,
    SqlFaqRepository,
)
from tee_concierge.infrastructure.persistence.database import create_engine, create_sessionmaker
from tee_concierge.infrastructure.persistence.repository import (
    SqlConversationRepository,
    SqlMessageRepository,
)
from tee_concierge.infrastructure.queue.lock import RedisConversationLock
from tee_concierge.infrastructure.queue.rate_limiter import RedisRateLimiter
from tee_concierge.infrastructure.whatsapp.client import WhatsAppCloudGateway
from tee_concierge.infrastructure.whatsapp.fake import FakeGateway
from tee_concierge.logging import configure_logging

MAX_TRIES = 5
log = structlog.get_logger()


def build_gateway(settings: Settings, http: httpx.AsyncClient) -> MessageGateway:
    if settings.whatsapp_gateway == "cloud":
        return WhatsAppCloudGateway(
            http,
            settings.whatsapp_phone_number_id,
            settings.whatsapp_access_token.get_secret_value(),
            settings.whatsapp_api_version,
        )
    return FakeGateway()


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_engine(settings.database_url)
    redis: Redis = Redis.from_url(settings.redis_url)
    http = httpx.AsyncClient(timeout=10.0)
    ctx.update(engine=engine, redis=redis, http=http)
    start_http_server(settings.metrics_port)
    sessions = create_sessionmaker(engine)
    ctx["process"] = ProcessInboundMessage(
        repo=SqlMessageRepository(sessions),
        gateway=build_gateway(settings, http),
        lock=RedisConversationLock(redis),
        responder=MenuEngine(
            conversations=SqlConversationRepository(sessions),
            catalog=SqlCatalogRepository(sessions),
            faq=SqlFaqRepository(sessions),
            usage=SqlUsageRepository(sessions),
            store=StoreInfo(
                name=settings.store_name,
                contact_phone=settings.store_contact_phone,
                hours=settings.store_hours,
            ),
        ),
        limiter=RedisRateLimiter(redis, settings.rate_limit_per_minute),
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["http"].aclose()
    await ctx["redis"].aclose()
    await ctx["engine"].dispose()


async def process_inbound(ctx: dict[str, Any], wamid: str) -> None:
    structlog.contextvars.bind_contextvars(wamid=wamid)  # correlation id on every log line
    try:
        with metrics.PROCESS_SECONDS.time():
            outcome: ProcessOutcome = await ctx["process"].execute(wamid)
        metrics.MESSAGES_PROCESSED.labels(outcome.value).inc()
    except Exception as exc:
        metrics.JOB_FAILURES.inc()
        log.exception("process_inbound_failed", attempt=ctx["job_try"])
        if ctx["job_try"] >= MAX_TRIES:
            raise
        raise Retry(defer=ctx["job_try"] ** 2 * 5) from exc
    finally:
        structlog.contextvars.clear_contextvars()


class WorkerSettings:
    functions = [process_inbound]  # noqa: RUF012
    on_startup = startup
    on_shutdown = shutdown
    max_tries = MAX_TRIES
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
