from decimal import Decimal

from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine import catalog_nodes
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.catalog import format_price
from tee_concierge.domain.messaging import Reply, ReplyKind
from tests.fakes import InMemoryCatalog, InMemoryFaq

STORE = StoreInfo(name="Tee Concierge")
CATALOG = InMemoryCatalog()


def _ctx(*args: str) -> NodeContext:
    return NodeContext(STORE, CATALOG, InMemoryFaq(), args)


def _ids(reply: Reply) -> list[str]:
    return [o.id for o in reply.options]


def test_prices_are_formatted_as_soles() -> None:
    assert format_price(Decimal("59.9")) == "S/ 59.90"
    assert format_price(Decimal("1234.5")) == "S/ 1,234.50"


async def test_categories_come_from_the_catalog() -> None:
    reply = await catalog_nodes.catalog(_ctx())
    titles = [o.title for o in reply.options]
    assert titles[:3] == ["Básicas", "Estampadas", "Oversize"]
    assert reply.kind is ReplyKind.LIST


async def test_category_lists_products_with_price_and_material() -> None:
    reply = await catalog_nodes.category(_ctx("1", "0"))

    first = reply.options[0]
    assert first.title == "Polo Básico Negro"
    assert first.description is not None and "S/ 39.90" in first.description
    assert _ids(reply)[-2:] == ["go:catalog", "go:main"]


async def test_products_are_paginated_when_a_category_is_large() -> None:
    class Many(InMemoryCatalog):
        async def list_products(self, category_id: int, offset: int, limit: int):  # type: ignore[no-untyped-def]
            products, _ = await super().list_products(1, 0, 100)
            fake = [
                products[0].__class__(i, 1, f"Polo {i}", "", "", Decimal("10"))
                for i in range(1, 16)
            ]
            return fake[offset : offset + limit], len(fake)

    ctx = NodeContext(STORE, Many(), InMemoryFaq(), ("1", "0"))
    first = await catalog_nodes.category(ctx)
    last = await catalog_nodes.category(NodeContext(STORE, Many(), InMemoryFaq(), ("1", "2")))

    assert len(first.options) == 10 and encode("cat", "1", "1") in _ids(first)
    assert "página 1 de 3" in first.body
    assert encode("cat", "1", "3") not in _ids(last) and "página 3 de 3" in last.body


async def test_product_detail_offers_sizes_and_back_to_its_category() -> None:
    reply = await catalog_nodes.product(_ctx("4"))

    assert "Polo Machu Picchu" in reply.body and "S/ 59.90" in reply.body
    assert reply.kind is ReplyKind.BUTTONS
    assert _ids(reply) == ["go:variants:4", "go:cat:2:0", "go:main"]


async def test_sizes_show_available_colors_and_flag_sold_out_sizes() -> None:
    # Polo Básico Negro (id 1): XL has stock 0
    reply = await catalog_nodes.sizes(_ctx("1"))
    by_title = {o.title: o.description for o in reply.options}

    assert by_title["Talla M"] == "Negro"
    assert by_title["Talla XL"] == "Agotada"


async def test_stock_per_color_never_reveals_exact_numbers() -> None:
    # Polo Básico Colores (id 3): S/M/L stock 3 -> low, XL stock 1 -> low
    reply = await catalog_nodes.stock(_ctx("3", "M"))

    assert "Gris: ¡últimas unidades!" in reply.body
    assert not any(ch.isdigit() for ch in reply.body.split("Talla M")[1])


async def test_sold_out_and_available_labels() -> None:
    sold_out = await catalog_nodes.stock(_ctx("1", "XL"))
    plenty = await catalog_nodes.stock(_ctx("1", "M"))

    assert "Negro: agotado" in sold_out.body
    assert "Negro: disponible" in plenty.body


async def test_unknown_ids_fall_back_to_the_catalog_with_a_message() -> None:
    for node, args in (
        (catalog_nodes.product, ("999",)),
        (catalog_nodes.category, ("999", "0")),
        (catalog_nodes.sizes, ("abc",)),
        (catalog_nodes.stock, ("1",)),
    ):
        reply = await node(_ctx(*args))
        assert "ya no está disponible" in reply.body
        assert encode("cat", "1", "0") in _ids(reply)
