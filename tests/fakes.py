from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal

from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.domain.messaging import (
    ConversationState,
    HistoryMessage,
    InboundMessage,
    Reply,
    StatusUpdate,
    StoredReply,
)


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self.inbound: dict[str, InboundMessage] = {}
        self.processed: set[str] = set()
        self.outbound: list[tuple[str, Reply, str | None]] = []
        self.statuses: list[StatusUpdate] = []

    async def add_inbound(self, message: InboundMessage) -> bool:
        if message.wamid in self.inbound:
            return False
        self.inbound[message.wamid] = message
        return True

    async def get_unprocessed(self, wamid: str) -> InboundMessage | None:
        if wamid in self.processed:
            return None
        return self.inbound.get(wamid)

    async def mark_processed(self, wamid: str) -> None:
        self.processed.add(wamid)

    async def add_outbound(self, phone: str, reply: Reply, wamid: str | None) -> None:
        self.outbound.append((phone, reply, wamid))

    async def list_outbound(self, phone: str, after_id: int = 0) -> list[StoredReply]:
        return []

    async def update_status(self, update: StatusUpdate) -> bool:
        known = any(w == update.wamid for _, _, w in self.outbound)
        if known:
            self.statuses.append(update)
        return known

    async def list_history(
        self, phone: str, limit: int = 50, before_id: int | None = None
    ) -> list[HistoryMessage]:
        return []


class RecordingQueue:
    def __init__(self, fail_times: int = 0) -> None:
        self.jobs: list[str] = []
        self._fail_times = fail_times

    async def enqueue_inbound(self, wamid: str) -> None:
        if self._fail_times:
            self._fail_times -= 1
            raise ConnectionError("redis down")
        self.jobs.append(wamid)


class RecordingGateway:
    def __init__(self) -> None:
        self.sent: list[tuple[str, Reply]] = []
        self.read: list[str] = []
        self.fail_mark_read = False

    async def mark_read(self, wamid: str) -> None:
        if self.fail_mark_read:
            raise ConnectionError("graph api down")
        self.read.append(wamid)

    async def send(self, to: str, reply: Reply) -> str | None:
        self.sent.append((to, reply))
        return f"out.{len(self.sent)}"


class NoopLock:
    @asynccontextmanager
    async def hold(self, key: str) -> AsyncIterator[None]:
        yield


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self.states: dict[str, ConversationState] = {}

    async def get(self, phone: str) -> ConversationState | None:
        return self.states.get(phone)

    async def save(self, state: ConversationState) -> None:
        self.states[state.phone] = state


class InMemoryCatalog:
    """Built from the same demo data as the seed script."""

    def __init__(self, products_per_category_limit: int | None = None) -> None:
        from tee_concierge.seed import DEMO_PRODUCTS, SIZES

        self.categories: list[Category] = []
        self.products: list[Product] = []
        self.variants: list[Variant] = []
        for category, name, desc, material, price, colors, stocks in DEMO_PRODUCTS:
            cat = next((c for c in self.categories if c.name == category), None)
            if cat is None:
                cat = Category(len(self.categories) + 1, category)
                self.categories.append(cat)
            product = Product(len(self.products) + 1, cat.id, name, desc, material, Decimal(price))
            self.products.append(product)
            for size, stock in zip(SIZES, stocks, strict=True):
                for color in colors:
                    n = len(self.variants) + 1
                    self.variants.append(Variant(n, product.id, f"SKU-{n}", size, color, stock))

    async def list_categories(self) -> list[Category]:
        return list(self.categories)

    async def get_category(self, category_id: int) -> Category | None:
        return next((c for c in self.categories if c.id == category_id), None)

    async def list_products(
        self, category_id: int, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        mine = [p for p in self.products if p.category_id == category_id]
        return mine[offset : offset + limit], len(mine)

    async def get_product(self, product_id: int) -> Product | None:
        return next((p for p in self.products if p.id == product_id), None)

    async def list_variants(self, product_id: int) -> list[Variant]:
        return [v for v in self.variants if v.product_id == product_id]


class InMemoryFaq:
    def __init__(self, entries: dict[str, str] | None = None) -> None:
        self.entries = entries or {}

    async def get(self, topic: str) -> str | None:
        return self.entries.get(topic)
