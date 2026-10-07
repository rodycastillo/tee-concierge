"""Synthetic demo catalog (for the T-shirt store example). Fake data only: this repo is public.

Only businesses whose menu has a `catalog` node use it; others never need to run this.

Run with `make seed` (or `python -m tee_concierge.seed`). Idempotent: it does nothing
when categories already exist, so it never overwrites real data.
"""

import asyncio
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tee_concierge.config import get_settings
from tee_concierge.infrastructure.persistence.database import create_engine, create_sessionmaker
from tee_concierge.infrastructure.persistence.models import (
    CategoryRow,
    ProductRow,
    VariantRow,
)

SIZES = ("S", "M", "L", "XL")

# (category, name, description, material, price, colors, stock pattern per size)
DEMO_PRODUCTS: tuple[tuple[str, str, str, str, str, tuple[str, ...], tuple[int, ...]], ...] = (
    (
        "Básicas",
        "Polo Básico Negro",
        "Corte clásico, cuello redondo.",
        "Algodón pima 100%",
        "39.90",
        ("Negro",),
        (8, 12, 6, 0),
    ),
    (
        "Básicas",
        "Polo Básico Blanco",
        "Fresco y versátil para todos los días.",
        "Algodón pima 100%",
        "39.90",
        ("Blanco",),
        (5, 9, 2, 4),
    ),
    (
        "Básicas",
        "Polo Básico Colores",
        "Tres colores para combinar.",
        "Algodón peinado",
        "44.90",
        ("Gris", "Azul", "Verde"),
        (3, 3, 3, 1),
    ),
    (
        "Estampadas",
        "Polo Machu Picchu",
        "Estampado artesanal inspirado en el Cusco.",
        "Algodón pima 100%",
        "59.90",
        ("Negro", "Beige"),
        (4, 6, 5, 2),
    ),
    (
        "Estampadas",
        "Polo Cóndor Andino",
        "Diseño exclusivo, edición limitada.",
        "Algodón orgánico",
        "64.90",
        ("Blanco",),
        (2, 3, 1, 0),
    ),
    (
        "Estampadas",
        "Polo Lima Vintage",
        "Gráfico retro de la ciudad.",
        "Algodón peinado",
        "54.90",
        ("Negro", "Rojo"),
        (6, 6, 4, 3),
    ),
    (
        "Oversize",
        "Polo Oversize Arena",
        "Caída holgada, estilo urbano.",
        "Algodón pesado 220g",
        "69.90",
        ("Arena",),
        (3, 5, 5, 3),
    ),
    (
        "Oversize",
        "Polo Oversize Grafito",
        "Máxima comodidad, tela gruesa.",
        "Algodón pesado 220g",
        "69.90",
        ("Grafito", "Negro"),
        (0, 4, 4, 2),
    ),
)


async def seed(sessions: async_sessionmaker[AsyncSession]) -> bool:
    """Insert the demo data. Returns False when the database already has a catalog."""
    async with sessions() as session, session.begin():
        existing = await session.scalar(select(func.count()).select_from(CategoryRow))
        if existing:
            return False
        categories: dict[str, CategoryRow] = {}
        for category, *_rest in DEMO_PRODUCTS:
            if category not in categories:
                categories[category] = CategoryRow(name=category, position=len(categories))
                session.add(categories[category])
        await session.flush()
        for index, (category, name, desc, material, price, colors, stocks) in enumerate(
            DEMO_PRODUCTS, start=1
        ):
            product = ProductRow(
                category_id=categories[category].id,
                name=name,
                description=desc,
                material=material,
                price=Decimal(price),
            )
            session.add(product)
            await session.flush()
            for size, stock in zip(SIZES, stocks, strict=True):
                for color in colors:
                    session.add(
                        VariantRow(
                            product_id=product.id,
                            sku=f"TC-{index:03d}-{color[:3].upper()}-{size}",
                            size=size,
                            color=color,
                            stock=stock,
                        )
                    )
    return True


async def _main() -> None:
    engine = create_engine(get_settings().database_url)
    try:
        created = await seed(create_sessionmaker(engine))
    finally:
        await engine.dispose()
    print("Demo catalog created." if created else "Catalog already has data; nothing to do.")


if __name__ == "__main__":
    asyncio.run(_main())
