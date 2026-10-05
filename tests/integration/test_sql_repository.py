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
