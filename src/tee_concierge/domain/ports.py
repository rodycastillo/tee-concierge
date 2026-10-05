from contextlib import AbstractAsyncContextManager
from typing import Protocol

from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.domain.messaging import (
    ConversationState,
    HistoryMessage,
    InboundMessage,
    Reply,
    StatusUpdate,
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

    async def update_status(self, update: StatusUpdate) -> bool:
        """Apply a delivery status to an outbound message. Statuses never move backwards.
        Returns False if the message is unknown."""
        ...

    async def list_history(
        self, phone: str, limit: int = 50, before_id: int | None = None
    ) -> list[HistoryMessage]:
        """Both directions, newest first."""
        ...


class ConversationRepository(Protocol):
    async def get(self, phone: str) -> ConversationState | None: ...

    async def save(self, state: ConversationState) -> None: ...


class CatalogRepository(Protocol):
    async def list_categories(self) -> list[Category]: ...

    async def get_category(self, category_id: int) -> Category | None: ...

    async def list_products(
        self, category_id: int, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        """Active products of a category, plus the total count (for pagination)."""
        ...

    async def get_product(self, product_id: int) -> Product | None: ...

    async def list_variants(self, product_id: int) -> list[Variant]: ...


class FaqRepository(Protocol):
    async def get(self, topic: str) -> str | None:
        """Editable answer for a topic (sizes, shipping, payment, returns), if set."""
        ...


class JobQueue(Protocol):
    async def enqueue_inbound(self, wamid: str) -> None:
        """Schedule processing. Must be idempotent per wamid."""
        ...


class MessageGateway(Protocol):
    async def send(self, to: str, reply: Reply) -> str | None:
        """Send a text, buttons or list message. Returns the provider's message id."""
        ...

    async def mark_read(self, wamid: str) -> None:
        """Show the customer the blue ticks for an inbound message."""
        ...


class ConversationLock(Protocol):
    def hold(self, key: str) -> AbstractAsyncContextManager[None]:
        """Serialize processing per conversation."""
        ...
