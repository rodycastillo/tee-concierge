from contextlib import AbstractAsyncContextManager
from typing import Protocol

from tee_concierge.domain.messaging import (
    ConversationState,
    InboundMessage,
    Reply,
    StoredReply,
)


class MessageRepository(Protocol):
    async def add_inbound(self, message: InboundMessage) -> bool:
        """Persist the message. Returns False if its wamid was already stored."""
        ...

    async def get_unprocessed(self, wamid: str) -> InboundMessage | None:
        """The inbound message, or None if unknown or already processed."""
        ...

    async def mark_processed(self, wamid: str) -> None: ...

    async def add_outbound(self, phone: str, reply: Reply, wamid: str | None) -> None: ...

    async def list_outbound(self, phone: str, after_id: int = 0) -> list[StoredReply]: ...


class ConversationRepository(Protocol):
    async def get(self, phone: str) -> ConversationState | None: ...

    async def save(self, state: ConversationState) -> None: ...


class JobQueue(Protocol):
    async def enqueue_inbound(self, wamid: str) -> None:
        """Schedule processing. Must be idempotent per wamid."""
        ...


class MessageGateway(Protocol):
    async def send(self, to: str, reply: Reply) -> str | None:
        """Send a text, buttons or list message. Returns the provider's message id."""
        ...


class ConversationLock(Protocol):
    def hold(self, key: str) -> AbstractAsyncContextManager[None]:
        """Serialize processing per conversation."""
        ...
