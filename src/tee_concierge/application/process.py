from typing import Protocol

import structlog

from tee_concierge.domain.messaging import InboundMessage, Reply
from tee_concierge.domain.ports import ConversationLock, MessageGateway, MessageRepository

log = structlog.get_logger()


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
    ) -> None:
        self._repo = repo
        self._gateway = gateway
        self._lock = lock
        self._responder = responder

    async def _mark_read(self, wamid: str) -> None:
        try:
            await self._gateway.mark_read(wamid)
        except Exception:  # cosmetic: never block the reply because of blue ticks
            log.warning("mark_read_failed", wamid=wamid, exc_info=True)

    async def execute(self, wamid: str) -> None:
        message = await self._repo.get_unprocessed(wamid)
        if message is None:
            log.info("skip_processed_or_unknown", wamid=wamid)
            return
        async with self._lock.hold(message.phone):
            # Re-check inside the lock: a concurrent job may have handled it.
            message = await self._repo.get_unprocessed(wamid)
            if message is None:
                return
            await self._mark_read(wamid)
            reply = await self._responder.reply_to(message)
            sent_id = await self._gateway.send(message.phone, reply)
            await self._repo.add_outbound(message.phone, reply, sent_id)
            await self._repo.mark_processed(wamid)
            log.info("message_processed", wamid=wamid)
