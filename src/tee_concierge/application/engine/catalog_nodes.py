"""Catalog screens: categories -> products (paginated) -> detail -> sizes -> stock by color.

Only registered when the business's menu contains a `catalog` node.
"""

from tee_concierge.application.content.messages import fill
from tee_concierge.application.engine.nav import MAIN, go
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.catalog import (
    LOW_STOCK_THRESHOLD,
    Variant,
    format_price,
    size_sort_key,
)
from tee_concierge.domain.messaging import MAX_LIST_ROWS, ROW_TITLE_MAX, Option, Reply

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


def _entry(ctx: NodeContext) -> str:
    """Id of the business's `catalog` node, the 'home' of these screens."""
    assert ctx.nav.catalog is not None  # noqa: S101 - screens are only registered with it
    return ctx.nav.catalog


def _contact(ctx: NodeContext) -> list[Option]:
    return [go(ctx.nav.contact, ctx.messages.label_contact)] if ctx.nav.contact else []


async def _not_available(ctx: NodeContext) -> Reply:
    return await catalog(ctx, prefix=ctx.messages.not_available)


async def catalog(ctx: NodeContext, prefix: str | None = None) -> Reply:
    m = ctx.messages
    categories = await ctx.catalog.list_categories()
    if not categories:
        return Reply(m.catalog_empty, (go(MAIN, m.label_main), *_contact(ctx)))
    body = (
        m.catalog_choose_category if prefix is None else f"{prefix}\n\n{m.catalog_choose_category}"
    )
    options = [
        Option(encode(CATEGORY, str(c.id), "0"), _truncate(c.name, ROW_TITLE_MAX))
        for c in categories[: MAX_LIST_ROWS - 2]
    ]
    options += [go(MAIN, m.label_main), *_contact(ctx)]
    return Reply(body, tuple(options))


async def category(ctx: NodeContext) -> Reply:
    m = ctx.messages
    category_id, page = _int(ctx.args, 0), _int(ctx.args, 1) or 0
    found = await ctx.catalog.get_category(category_id) if category_id is not None else None
    if found is None:
        return await _not_available(ctx)
    products, total = await ctx.catalog.list_products(found.id, page * PAGE_SIZE, PAGE_SIZE)
    if not products:
        return await (_not_available(ctx) if page else catalog(ctx, prefix=m.catalog_empty))
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
        options.append(Option(encode(CATEGORY, str(found.id), str(page + 1)), m.label_more))
    options += [go(_entry(ctx), m.label_back), go(MAIN, m.label_main)]
    suffix = fill(m.page_suffix, page=page + 1, pages=pages) if pages > 1 else ""
    return Reply(fill(m.choose_product, category=found.name, page=suffix), tuple(options))


def _detail(name: str, price: str, material: str, description: str) -> str:
    lines = [f"*{name}*", f"💰 {price}"]
    if material:
        lines.append(f"🧵 {material}")
    if description:
        lines.append(f"\n{description}")
    return "\n".join(lines)


async def product(ctx: NodeContext) -> Reply:
    m = ctx.messages
    product_id = _int(ctx.args, 0)
    found = await ctx.catalog.get_product(product_id) if product_id is not None else None
    if found is None:
        return await _not_available(ctx)
    return Reply(
        _detail(found.name, format_price(found.price), found.material, found.description),
        (
            Option(encode(SIZES, str(found.id)), m.label_sizes_colors),
            Option(encode(CATEGORY, str(found.category_id), "0"), m.label_back),
            go(MAIN, m.label_main),
        ),
        image_url=found.image_url,
    )


async def sizes(ctx: NodeContext) -> Reply:
    m = ctx.messages
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
                fill(m.size_label, size=size),
                _truncate(", ".join(colors), 72) if colors else m.size_sold_out,
            )
        )
    options += [Option(encode(PRODUCT, str(found.id)), m.label_back), go(MAIN, m.label_main)]
    options += _contact(ctx)
    return Reply(fill(m.choose_size, product=found.name), tuple(options))


def _stock_label(ctx: NodeContext, stock: int) -> str:
    if stock <= 0:
        return ctx.messages.stock_out
    return ctx.messages.stock_low if stock <= LOW_STOCK_THRESHOLD else ctx.messages.stock_available


async def stock(ctx: NodeContext) -> Reply:
    m = ctx.messages
    product_id = _int(ctx.args, 0)
    size = ctx.args[1] if len(ctx.args) > 1 else None
    found = await ctx.catalog.get_product(product_id) if product_id is not None else None
    if found is None or size is None:
        return await _not_available(ctx)
    variants = [v for v in await ctx.catalog.list_variants(found.id) if v.size == size]
    if not variants:
        return await sizes(
            NodeContext(ctx.business, ctx.catalog, ctx.messages, ctx.nav, (str(found.id),))
        )
    lines = [f"• {v.color}: {_stock_label(ctx, v.stock)}" for v in variants]
    text = fill(m.stock_header, product=found.name, size=size) + "\n\n" + "\n".join(lines)
    return Reply(
        text if len(text) <= 1000 else text[:999].rstrip() + "…",
        (
            Option(encode(SIZES, str(found.id)), m.label_other_size),
            go(MAIN, m.label_main),
            *_contact(ctx),
        ),
    )
