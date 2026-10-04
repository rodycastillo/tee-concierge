from typing import Protocol

import structlog

from tee_concierge.domain.messaging import InboundMessage, MessageType
from tee_concierge.domain.ports import ConversationLock, MessageGateway, MessageRepository

log = structlog.get_logger()


class Responder(Protocol):
    async def reply_to(self, message: InboundMessage) -> str: ...


class EchoResponder:
    """Phase 2 placeholder. Phase 3 replaces it with the menu engine."""

    async def reply_to(self, message: InboundMessage) -> str:
        if message.type is MessageType.UNSUPPORTED:
            return "Por ahora solo puedo leer mensajes de texto 🙂"
        return f"Recibido: {message.text or message.reply_id}"


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
            body = await self._responder.reply_to(message)
            sent_id = await self._gateway.send_text(message.phone, body)
            await self._repo.add_outbound(message.phone, body, sent_id)
            await self._repo.mark_processed(wamid)
            log.info("message_processed", wamid=wamid)
