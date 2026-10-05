from enum import StrEnum
from typing import Protocol

import structlog

from tee_concierge.domain.messaging import InboundMessage, Reply
from tee_concierge.domain.ports import (
    ConversationLock,
    MessageGateway,
    MessageRepository,
    RateLimiter,
)

log = structlog.get_logger()


class ProcessOutcome(StrEnum):
    REPLIED = "replied"
    SKIPPED = "skipped"  # unknown or already processed
    RATE_LIMITED = "rate_limited"


class Responder(Protocol):
    async def reply_to(self, message: InboundMessage) -> Reply: ...


class ProcessInboundMessage:
    """Reply to one stored inbound message, at most one conversation step at a time.

    Delivery is at-least-once: if the process dies after sending but before
    marking the message processed, a retry sends the reply again.
    """

    def __init__(
        self,
        repo: MessageRepository,
        gateway: MessageGateway,
        lock: ConversationLock,
        responder: Responder,
        limiter: RateLimiter,
    ) -> None:
        self._repo = repo
        self._gateway = gateway
        self._lock = lock
        self._responder = responder
        self._limiter = limiter

    async def _mark_read(self, wamid: str) -> None:
        try:
            await self._gateway.mark_read(wamid)
        except Exception:  # cosmetic: never block the reply because of blue ticks
            log.warning("mark_read_failed", wamid=wamid, exc_info=True)

    async def execute(self, wamid: str) -> ProcessOutcome:
        message = await self._repo.get_unprocessed(wamid)
        if message is None:
            log.info("skip_processed_or_unknown", wamid=wamid)
            return ProcessOutcome.SKIPPED
        if not await self._limiter.allow(message.phone):
            # Drop silently: replying to a flood would only feed it.
            await self._repo.mark_processed(wamid)
            log.warning("rate_limited", wamid=wamid, phone_suffix=message.phone[-4:])
            return ProcessOutcome.RATE_LIMITED
        async with self._lock.hold(message.phone):
            # Re-check inside the lock: a concurrent job may have handled it.
            message = await self._repo.get_unprocessed(wamid)
            if message is None:
                return ProcessOutcome.SKIPPED
            await self._mark_read(wamid)
            reply = await self._responder.reply_to(message)
            sent_id = await self._gateway.send(message.phone, reply)
            await self._repo.add_outbound(message.phone, reply, sent_id)
            await self._repo.mark_processed(wamid)
            log.info("message_processed", wamid=wamid)
            return ProcessOutcome.REPLIED
