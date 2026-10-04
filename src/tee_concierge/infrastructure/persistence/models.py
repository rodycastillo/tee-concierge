from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class MessageRow(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_phone_id", "phone", "id"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True
    )
    wamid: Mapped[str | None] = mapped_column(String(128), unique=True)
    direction: Mapped[str] = mapped_column(String(3))  # "in" | "out"
    phone: Mapped[str] = mapped_column(String(32))
    type: Mapped[str] = mapped_column(String(32))
    body: Mapped[str | None] = mapped_column(Text)
    reply_id: Mapped[str | None] = mapped_column(String(200))
    profile_name: Mapped[str | None] = mapped_column(String(128))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
