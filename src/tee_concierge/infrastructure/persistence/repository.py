from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tee_concierge.domain.messaging import (
    ConversationState,
    InboundMessage,
    MessageType,
    Option,
    Reply,
    StoredReply,
)
from tee_concierge.infrastructure.persistence.models import ConversationRow, MessageRow


class SqlMessageRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add_inbound(self, message: InboundMessage) -> bool:
        row = MessageRow(
            wamid=message.wamid,
            direction="in",
            phone=message.phone,
            type=message.type.value,
            body=message.text,
            reply_id=message.reply_id,
            profile_name=message.profile_name,
            sent_at=message.sent_at,
        )
        try:
            async with self._sessions() as session, session.begin():
                session.add(row)
        except IntegrityError:
            return False  # unique wamid: already stored
        return True

    async def get_unprocessed(self, wamid: str) -> InboundMessage | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(MessageRow).where(
                    MessageRow.wamid == wamid,
                    MessageRow.direction == "in",
                    MessageRow.processed_at.is_(None),
                )
            )
        if row is None:
            return None
        return InboundMessage(
            wamid=wamid,
            phone=row.phone,
            type=MessageType(row.type),
            sent_at=row.sent_at,
            text=row.body,
            reply_id=row.reply_id,
            profile_name=row.profile_name,
        )

    async def mark_processed(self, wamid: str) -> None:
        async with self._sessions() as session, session.begin():
            await session.execute(
                update(MessageRow)
                .where(MessageRow.wamid == wamid, MessageRow.direction == "in")
                .values(processed_at=datetime.now(UTC))
            )

    async def add_outbound(self, phone: str, reply: Reply, wamid: str | None) -> None:
        now = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            session.add(
                MessageRow(
                    wamid=wamid,
                    direction="out",
                    phone=phone,
                    type=reply.kind.value,
                    body=reply.body,
                    options=[
                        {"id": o.id, "title": o.title, "description": o.description}
                        for o in reply.options
                    ],
                    sent_at=now,
                    processed_at=now,
                )
            )

    async def list_outbound(self, phone: str, after_id: int = 0) -> list[StoredReply]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(MessageRow)
                .where(
                    MessageRow.phone == phone,
                    MessageRow.direction == "out",
                    MessageRow.id > after_id,
                )
                .order_by(MessageRow.id)
            )
            return [
                StoredReply(
                    id=r.id,
                    body=r.body or "",
                    options=tuple(
                        Option(o["id"], o["title"], o.get("description")) for o in r.options or []
                    ),
                    sent_at=r.sent_at,
                )
                for r in rows
            ]


class SqlConversationRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get(self, phone: str) -> ConversationState | None:
        async with self._sessions() as session:
            row = await session.get(ConversationRow, phone)
        if row is None:
            return None
        updated_at = row.updated_at
        if updated_at.tzinfo is None:  # SQLite drops tzinfo
            updated_at = updated_at.replace(tzinfo=UTC)
        return ConversationState(phone, row.node, row.failures, updated_at)

    async def save(self, state: ConversationState) -> None:
        updated_at = state.updated_at or datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            await session.merge(
                ConversationRow(
                    phone=state.phone,
                    node=state.node,
                    failures=state.failures,
                    updated_at=updated_at,
                )
            )
