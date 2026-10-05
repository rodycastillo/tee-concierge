from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from tee_concierge.domain.messaging import ConversationState, Option, Reply
from tee_concierge.infrastructure.persistence.database import create_sessionmaker
from tee_concierge.infrastructure.persistence.models import Base
from tee_concierge.infrastructure.persistence.repository import (
    SqlConversationRepository,
    SqlMessageRepository,
)
from tee_concierge.infrastructure.whatsapp.parser import parse_inbound_messages
from tee_concierge.infrastructure.whatsapp.simulator import text_payload


@pytest.fixture
async def repo(tmp_path: Path) -> AsyncIterator[SqlMessageRepository]:
    # SQLite keeps this runnable without Docker; the unique constraint behaves the same.
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield SqlMessageRepository(create_sessionmaker(engine))
    await engine.dispose()


async def test_duplicate_wamid_is_rejected_by_the_unique_constraint(
    repo: SqlMessageRepository,
) -> None:
    [msg] = parse_inbound_messages(text_payload("51911111111", "Hola", "wamid.1"))

    assert await repo.add_inbound(msg) is True
    assert await repo.add_inbound(msg) is False


async def test_processed_message_is_no_longer_returned(repo: SqlMessageRepository) -> None:
    [msg] = parse_inbound_messages(text_payload("51911111111", "Hola", "wamid.1"))
    await repo.add_inbound(msg)

    loaded = await repo.get_unprocessed("wamid.1")
    assert loaded is not None and loaded.text == "Hola"

    await repo.mark_processed("wamid.1")
    assert await repo.get_unprocessed("wamid.1") is None


async def test_outbox_lists_only_new_replies_for_that_phone(repo: SqlMessageRepository) -> None:
    await repo.add_outbound("51911111111", Reply("uno"), "o1")
    await repo.add_outbound("51922222222", Reply("otro cliente"), "o2")
    await repo.add_outbound("51911111111", Reply("dos", (Option("go:main", "Menú"),)), "o3")

    all_replies = await repo.list_outbound("51911111111")
    newer = await repo.list_outbound("51911111111", after_id=all_replies[0].id)

    assert [r.body for r in all_replies] == ["uno", "dos"]
    assert [r.body for r in newer] == ["dos"]
    assert newer[0].options == (Option("go:main", "Menú"),)


async def test_conversation_state_round_trips_and_updates(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/conv.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    conversations = SqlConversationRepository(create_sessionmaker(engine))

    assert await conversations.get("51911111111") is None
    await conversations.save(
        ConversationState("51911111111", "shipping", 1, datetime(2026, 1, 1, tzinfo=UTC))
    )
    await conversations.save(
        ConversationState("51911111111", "main", 0, datetime(2026, 1, 2, tzinfo=UTC))
    )

    state = await conversations.get("51911111111")
    assert state == ConversationState("51911111111", "main", 0, datetime(2026, 1, 2, tzinfo=UTC))
    await engine.dispose()


async def test_catalog_queries_and_seed_are_idempotent(tmp_path: Path) -> None:
    from tee_concierge.infrastructure.persistence.catalog_repository import (
        SqlCatalogRepository,
        SqlFaqRepository,
    )
    from tee_concierge.seed import seed

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/catalog.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = create_sessionmaker(engine)

    assert await seed(sessions) is True
    assert await seed(sessions) is False  # never overwrites existing data

    catalog = SqlCatalogRepository(sessions)
    categories = await catalog.list_categories()
    assert [c.name for c in categories] == ["Básicas", "Estampadas", "Oversize"]
    products, total = await catalog.list_products(categories[0].id, offset=1, limit=2)
    assert total == 3 and len(products) == 2
    variants = await catalog.list_variants(products[0].id)
    assert {v.size for v in variants} == {"S", "M", "L", "XL"}
    assert await catalog.get_product(99999) is None
    assert await SqlFaqRepository(sessions).get("shipping") is not None
    assert await SqlFaqRepository(sessions).get("nope") is None
    await engine.dispose()


async def test_delivery_status_only_moves_forward_and_history_lists_both_directions(
    repo: SqlMessageRepository,
) -> None:
    from tee_concierge.domain.messaging import DeliveryStatus, StatusUpdate

    at = datetime(2026, 10, 5, tzinfo=UTC)
    [msg] = parse_inbound_messages(text_payload("51911111111", "Hola", "in.1"))
    await repo.add_inbound(msg)
    await repo.add_outbound("51911111111", Reply("Hola!"), "out.1")

    def status(value: DeliveryStatus, error: str | None = None) -> StatusUpdate:
        return StatusUpdate("out.1", value, at, error)

    async def current() -> str | None:
        return next(
            m for m in await repo.list_history("51911111111") if m.direction == "out"
        ).status

    assert await current() == "accepted"
    assert await repo.update_status(status(DeliveryStatus.READ)) is True
    await repo.update_status(status(DeliveryStatus.DELIVERED))  # late, out of order
    assert await current() == "read"
    await repo.update_status(status(DeliveryStatus.FAILED, "late"))  # must not overwrite read
    assert await current() == "read"
    assert await repo.update_status(StatusUpdate("nope", DeliveryStatus.SENT, at)) is False

    history = await repo.list_history("51911111111")
    assert [m.direction for m in history] == ["out", "in"]  # newest first
    older = await repo.list_history("51911111111", before_id=history[0].id)
    assert [m.direction for m in older] == ["in"]


async def test_failed_status_is_recorded_when_nothing_better_happened(
    repo: SqlMessageRepository,
) -> None:
    from tee_concierge.domain.messaging import DeliveryStatus, StatusUpdate

    await repo.add_outbound("51911111111", Reply("Hola!"), "out.1")
    await repo.update_status(
        StatusUpdate("out.1", DeliveryStatus.FAILED, datetime(2026, 10, 5, tzinfo=UTC), "no wa")
    )

    [row] = await repo.list_history("51911111111")
    assert row.status == "failed"


async def test_usage_counters_increment_and_summarize(
    repo: SqlMessageRepository, tmp_path: Path
) -> None:
    from tee_concierge.infrastructure.persistence.admin_repository import SqlUsageRepository

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/usage.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = create_sessionmaker(engine)
    usage, messages = SqlUsageRepository(sessions), SqlMessageRepository(sessions)

    for node in ("main", "shipping", "main", "main", "shipping", "catalog"):
        await usage.record_visit(node)
    [msg] = parse_inbound_messages(text_payload("51911111111", "Hola", "w1"))
    await messages.add_inbound(msg)
    await messages.add_outbound("51911111111", Reply("hola"), "o1")

    summary = await usage.summary(top=2)

    assert summary.top_nodes == [("main", 3), ("shipping", 2)]
    assert (summary.inbound_messages, summary.outbound_messages, summary.customers) == (1, 1, 1)
    await engine.dispose()
