from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
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
    type: Mapped[str] = mapped_column(String(32))  # inbound type or outbound reply kind
    body: Mapped[str | None] = mapped_column(Text)
    reply_id: Mapped[str | None] = mapped_column(String(200))
    options: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)  # outbound options
    profile_name: Mapped[str | None] = mapped_column(String(128))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(16))  # outbound delivery status
    status_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_error: Mapped[str | None] = mapped_column(String(200))


class ConversationRow(Base):
    __tablename__ = "conversations"

    phone: Mapped[str] = mapped_column(String(32), primary_key=True)
    node: Mapped[str] = mapped_column(String(64))
    failures: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CategoryRow(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductRow(Base):
    __tablename__ = "products"
    __table_args__ = (Index("ix_products_category_active", "category_id", "active"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    material: Mapped[str] = mapped_column(String(120), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    image_url: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class VariantRow(Base):
    __tablename__ = "variants"
    __table_args__ = (
        UniqueConstraint("product_id", "size", "color", name="uq_variant_product_size_color"),
        CheckConstraint("stock >= 0", name="ck_variant_stock_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    size: Mapped[str] = mapped_column(String(8))
    color: Mapped[str] = mapped_column(String(40))
    stock: Mapped[int] = mapped_column(Integer, default=0)


class NodeVisitRow(Base):
    __tablename__ = "node_visits"

    node: Mapped[str] = mapped_column(String(64), primary_key=True)
    visits: Mapped[int] = mapped_column(BigInteger().with_variant(Integer(), "sqlite"), default=0)


class FaqRow(Base):
    __tablename__ = "faq_entries"

    topic: Mapped[str] = mapped_column(String(40), primary_key=True)
    body: Mapped[str] = mapped_column(Text)
