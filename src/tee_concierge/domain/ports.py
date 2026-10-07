from contextlib import AbstractAsyncContextManager
from decimal import Decimal
from typing import Any, Protocol

from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.domain.messaging import (
    ConversationState,
    HistoryMessage,
    InboundMessage,
    Reply,
    StatusUpdate,
    StoredReply,
    UsageSummary,
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


class AdminCatalogRepository(Protocol):
    """Write side of the catalog, used by the admin API."""

    async def create_category(self, name: str) -> Category: ...

    async def list_all_products(self, offset: int, limit: int) -> list[Product]:
        """Including inactive products."""
        ...

    async def create_product(
        self,
        category_id: int,
        name: str,
        description: str,
        material: str,
        price: Decimal,
        image_url: str | None,
    ) -> Product: ...

    async def update_product(self, product_id: int, changes: dict[str, Any]) -> Product: ...

    async def create_variant(
        self, product_id: int, sku: str, size: str, color: str, stock: int
    ) -> Variant: ...

    async def set_stock(self, variant_id: int, stock: int) -> Variant: ...


class UsageRepository(Protocol):
    async def record_visit(self, node: str) -> None: ...

    async def summary(self, top: int = 10) -> UsageSummary: ...


class RateLimiter(Protocol):
    async def allow(self, key: str) -> bool:
        """Count one event for `key`; False once it exceeds the allowed rate."""
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
