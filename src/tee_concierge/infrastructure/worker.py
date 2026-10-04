from typing import Any

import httpx
from arq import Retry
from arq.connections import RedisSettings
from redis.asyncio import Redis

from tee_concierge.application.process import EchoResponder, ProcessInboundMessage
from tee_concierge.config import Settings, get_settings
from tee_concierge.domain.ports import MessageGateway
from tee_concierge.infrastructure.persistence.database import create_engine, create_sessionmaker
from tee_concierge.infrastructure.persistence.repository import SqlMessageRepository
from tee_concierge.infrastructure.queue.lock import RedisConversationLock
from tee_concierge.infrastructure.whatsapp.client import WhatsAppCloudGateway
from tee_concierge.infrastructure.whatsapp.fake import FakeGateway
from tee_concierge.logging import configure_logging

MAX_TRIES = 5


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
    ctx["process"] = ProcessInboundMessage(
        repo=SqlMessageRepository(create_sessionmaker(engine)),
        gateway=build_gateway(settings, http),
        lock=RedisConversationLock(redis),
        responder=EchoResponder(),
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["http"].aclose()
    await ctx["redis"].aclose()
    await ctx["engine"].dispose()


async def process_inbound(ctx: dict[str, Any], wamid: str) -> None:
    try:
        await ctx["process"].execute(wamid)
    except Exception as exc:
        if ctx["job_try"] >= MAX_TRIES:
            raise
        raise Retry(defer=ctx["job_try"] ** 2 * 5) from exc


class WorkerSettings:
    functions = [process_inbound]  # noqa: RUF012
    on_startup = startup
    on_shutdown = shutdown
    max_tries = MAX_TRIES
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
