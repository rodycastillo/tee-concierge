"""Catalog screens: categories -> products (paginated) -> detail -> sizes -> stock by color."""

from tee_concierge.application.content import es
from tee_concierge.application.engine.nav import CONTACT, MAIN, go
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.catalog import (
    LOW_STOCK_THRESHOLD,
    Variant,
    format_price,
    size_sort_key,
)
from tee_concierge.domain.messaging import MAX_LIST_ROWS, ROW_TITLE_MAX, Option, Reply

CATALOG = "catalog"
CATEGORY = "cat"
PRODUCT = "product"
SIZES = "variants"
STOCK = "stock"

# List rows: leave room for "Ver más", "Volver" and "Menú principal".
PAGE_SIZE = MAX_LIST_ROWS - 3


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _int(args: tuple[str, ...], index: int) -> int | None:
    try:
        return int(args[index])
    except (IndexError, ValueError):
        return None


async def _not_available(ctx: NodeContext) -> Reply:
    return await catalog(ctx, prefix=es.NOT_AVAILABLE)


async def catalog(ctx: NodeContext, prefix: str | None = None) -> Reply:
    categories = await ctx.catalog.list_categories()
    if not categories:
        return Reply(es.CATALOG_EMPTY, (go(MAIN, es.LABEL_MAIN), go(CONTACT, es.LABEL_CONTACT)))
    body = (
        es.CATALOG_CHOOSE_CATEGORY
        if prefix is None
        else f"{prefix}\n\n{es.CATALOG_CHOOSE_CATEGORY}"
    )
    options = [
        Option(encode(CATEGORY, str(c.id), "0"), _truncate(c.name, ROW_TITLE_MAX))
        for c in categories[: MAX_LIST_ROWS - 2]
    ]
    options += [go(MAIN, es.LABEL_MAIN), go(CONTACT, es.LABEL_CONTACT)]
    return Reply(body, tuple(options))


async def category(ctx: NodeContext) -> Reply:
    category_id, page = _int(ctx.args, 0), _int(ctx.args, 1) or 0
    found = await ctx.catalog.get_category(category_id) if category_id is not None else None
    if found is None:
        return await _not_available(ctx)
    products, total = await ctx.catalog.list_products(found.id, page * PAGE_SIZE, PAGE_SIZE)
    if not products:
        return await _not_available(ctx) if page else await catalog(ctx, prefix=es.CATALOG_EMPTY)
    pages = -(-total // PAGE_SIZE)
    options = [
        Option(
            encode(PRODUCT, str(p.id)),
            _truncate(p.name, ROW_TITLE_MAX),
            _truncate(f"{format_price(p.price)} · {p.material}".rstrip(" ·"), 72),
        )
        for p in products
    ]
    if (page + 1) * PAGE_SIZE < total:
        options.append(Option(encode(CATEGORY, str(found.id), str(page + 1)), es.LABEL_MORE))
    options += [go(CATALOG, es.LABEL_BACK), go(MAIN, es.LABEL_MAIN)]
    return Reply(es.choose_product(found.name, page, pages), tuple(options))


async def product(ctx: NodeContext) -> Reply:
    product_id = _int(ctx.args, 0)
    found = await ctx.catalog.get_product(product_id) if product_id is not None else None
    if found is None:
        return await _not_available(ctx)
    return Reply(
        es.product_detail(found.name, format_price(found.price), found.material, found.description),
        (
            Option(encode(SIZES, str(found.id)), es.LABEL_SIZES_COLORS),
            Option(encode(CATEGORY, str(found.category_id), "0"), es.LABEL_BACK),
            go(MAIN, es.LABEL_MAIN),
        ),
        image_url=found.image_url,
    )


async def sizes(ctx: NodeContext) -> Reply:
    product_id = _int(ctx.args, 0)
    found = await ctx.catalog.get_product(product_id) if product_id is not None else None
    if found is None:
        return await _not_available(ctx)
    by_size: dict[str, list[Variant]] = {}
    for variant in await ctx.catalog.list_variants(found.id):
        by_size.setdefault(variant.size, []).append(variant)
    options = []
    for size in sorted(by_size, key=size_sort_key)[: MAX_LIST_ROWS - 3]:
        colors = [v.color for v in by_size[size] if v.available]
        options.append(
            Option(
                encode(STOCK, str(found.id), size),
                f"Talla {size}",
                _truncate(", ".join(colors), 72) if colors else es.SIZE_SOLD_OUT,
            )
        )
    options += [
        Option(encode(PRODUCT, str(found.id)), es.LABEL_BACK),
        go(MAIN, es.LABEL_MAIN),
        go(CONTACT, es.LABEL_CONTACT),
    ]
    return Reply(es.choose_size(found.name), tuple(options))


def _stock_label(stock: int) -> str:
    if stock <= 0:
        return es.STOCK_OUT
    return es.STOCK_LOW if stock <= LOW_STOCK_THRESHOLD else es.STOCK_AVAILABLE


async def stock(ctx: NodeContext) -> Reply:
    product_id = _int(ctx.args, 0)
    size = ctx.args[1] if len(ctx.args) > 1 else None
    found = await ctx.catalog.get_product(product_id) if product_id is not None else None
    if found is None or size is None:
        return await _not_available(ctx)
    variants = [v for v in await ctx.catalog.list_variants(found.id) if v.size == size]
    if not variants:
        return await sizes(NodeContext(ctx.store, ctx.catalog, ctx.faq, (str(found.id),)))
    lines = [f"• {v.color}: {_stock_label(v.stock)}" for v in variants]
    return Reply(
        es.stock_for_size(found.name, size, lines),
        (
            Option(encode(SIZES, str(found.id)), es.LABEL_OTHER_SIZE),
            go(MAIN, es.LABEL_MAIN),
            go(CONTACT, es.LABEL_CONTACT),
        ),
    )
