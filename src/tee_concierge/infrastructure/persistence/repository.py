from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tee_concierge.domain.messaging import InboundMessage, MessageType, StoredReply
from tee_concierge.infrastructure.persistence.models import MessageRow


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

    async def add_outbound(self, phone: str, body: str, wamid: str | None) -> None:
        now = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            session.add(
                MessageRow(
                    wamid=wamid,
                    direction="out",
                    phone=phone,
                    type=MessageType.TEXT.value,
                    body=body,
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
            return [StoredReply(id=r.id, body=r.body or "", sent_at=r.sent_at) for r in rows]
