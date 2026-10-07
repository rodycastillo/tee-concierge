from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.infrastructure.persistence.models import (
    CategoryRow,
    ProductRow,
    VariantRow,
)


def _product(row: ProductRow) -> Product:
    return Product(
        row.id,
        row.category_id,
        row.name,
        row.description,
        row.material,
        row.price,
        row.image_url,
        row.active,
    )


class SqlCatalogRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def list_categories(self) -> list[Category]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(CategoryRow)
                .where(CategoryRow.active.is_(True))
                .order_by(CategoryRow.position, CategoryRow.id)
            )
            return [Category(r.id, r.name) for r in rows]

    async def get_category(self, category_id: int) -> Category | None:
        async with self._sessions() as session:
            row = await session.get(CategoryRow, category_id)
        return Category(row.id, row.name) if row and row.active else None

    async def list_products(
        self, category_id: int, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        where = (ProductRow.category_id == category_id, ProductRow.active.is_(True))
        async with self._sessions() as session:
            total = await session.scalar(select(func.count()).select_from(ProductRow).where(*where))
            rows = await session.scalars(
                select(ProductRow).where(*where).order_by(ProductRow.id).offset(offset).limit(limit)
            )
            return [_product(r) for r in rows], total or 0

    async def get_product(self, product_id: int) -> Product | None:
        async with self._sessions() as session:
            row = await session.get(ProductRow, product_id)
        return _product(row) if row and row.active else None

    async def list_variants(self, product_id: int) -> list[Variant]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(VariantRow)
                .where(VariantRow.product_id == product_id)
                .order_by(VariantRow.id)
            )
            return [Variant(r.id, r.product_id, r.sku, r.size, r.color, r.stock) for r in rows]
