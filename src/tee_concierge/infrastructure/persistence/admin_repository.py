from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.domain.errors import ConflictError, NotFoundError
from tee_concierge.domain.messaging import UsageSummary
from tee_concierge.infrastructure.persistence.catalog_repository import _product
from tee_concierge.infrastructure.persistence.models import (
    CategoryRow,
    MessageRow,
    NodeVisitRow,
    ProductRow,
    VariantRow,
)

_PRODUCT_FIELDS = {"name", "description", "material", "price", "image_url", "active", "category_id"}


def _variant(row: VariantRow) -> Variant:
    return Variant(row.id, row.product_id, row.sku, row.size, row.color, row.stock)


class SqlAdminCatalogRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create_category(self, name: str) -> Category:
        try:
            async with self._sessions() as session, session.begin():
                position = await session.scalar(
                    select(func.coalesce(func.max(CategoryRow.position), -1))
                )
                row = CategoryRow(name=name, position=(position or 0) + 1)
                session.add(row)
                await session.flush()
                return Category(row.id, row.name)
        except IntegrityError as exc:
            raise ConflictError(f"category {name!r} already exists") from exc

    async def list_all_products(self, offset: int, limit: int) -> list[Product]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(ProductRow).order_by(ProductRow.id).offset(offset).limit(limit)
            )
            return [_product(r) for r in rows]

    async def create_product(
        self,
        category_id: int,
        name: str,
        description: str,
        material: str,
        price: Decimal,
        image_url: str | None,
    ) -> Product:
        async with self._sessions() as session, session.begin():
            if await session.get(CategoryRow, category_id) is None:
                raise NotFoundError(f"category {category_id} not found")
            row = ProductRow(
                category_id=category_id,
                name=name,
                description=description,
                material=material,
                price=price,
                image_url=image_url,
            )
            session.add(row)
            await session.flush()
            return _product(row)

    async def update_product(self, product_id: int, changes: dict[str, Any]) -> Product:
        async with self._sessions() as session, session.begin():
            row = await session.get(ProductRow, product_id)
            if row is None:
                raise NotFoundError(f"product {product_id} not found")
            if (
                "category_id" in changes
                and await session.get(CategoryRow, changes["category_id"]) is None
            ):
                raise NotFoundError(f"category {changes['category_id']} not found")
            for key, value in changes.items():
                if key in _PRODUCT_FIELDS:
                    setattr(row, key, value)
            await session.flush()
            return _product(row)

    async def create_variant(
        self, product_id: int, sku: str, size: str, color: str, stock: int
    ) -> Variant:
        try:
            async with self._sessions() as session, session.begin():
                if await session.get(ProductRow, product_id) is None:
                    raise NotFoundError(f"product {product_id} not found")
                row = VariantRow(
                    product_id=product_id, sku=sku, size=size, color=color, stock=stock
                )
                session.add(row)
                await session.flush()
                return _variant(row)
        except IntegrityError as exc:
            raise ConflictError("sku or product/size/color already exists") from exc

    async def set_stock(self, variant_id: int, stock: int) -> Variant:
        async with self._sessions() as session, session.begin():
            row = await session.get(VariantRow, variant_id)
            if row is None:
                raise NotFoundError(f"variant {variant_id} not found")
            row.stock = stock
            await session.flush()
            return _variant(row)


class SqlUsageRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def record_visit(self, node: str) -> None:
        # Atomic increment; insert on first sight, retrying the update if two workers race.
        for _ in range(2):
            async with self._sessions() as session, session.begin():
                result = await session.execute(
                    update(NodeVisitRow)
                    .where(NodeVisitRow.node == node)
                    .values(visits=NodeVisitRow.visits + 1)
                )
                if result.rowcount:  # type: ignore[attr-defined]
                    return
            try:
                async with self._sessions() as session, session.begin():
                    session.add(NodeVisitRow(node=node, visits=1))
                return
            except IntegrityError:
                continue

    async def summary(self, top: int = 10) -> UsageSummary:
        async with self._sessions() as session:
            by_direction = await session.execute(
                select(MessageRow.direction, func.count()).group_by(MessageRow.direction)
            )
            counts = {direction: count for direction, count in by_direction.all()}
            customers = await session.scalar(select(func.count(func.distinct(MessageRow.phone))))
            nodes = await session.execute(
                select(NodeVisitRow.node, NodeVisitRow.visits)
                .order_by(NodeVisitRow.visits.desc(), NodeVisitRow.node)
                .limit(top)
            )
            return UsageSummary(
                inbound_messages=counts.get("in", 0),
                outbound_messages=counts.get("out", 0),
                customers=customers or 0,
                top_nodes=[(n, v) for n, v in nodes.all()],
            )
