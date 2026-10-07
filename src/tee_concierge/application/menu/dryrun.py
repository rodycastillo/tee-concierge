"""Renders every reachable screen of a menu once, to catch what a customer would hit.

Catches over-long text, links to nodes that don't exist and dead ends. Catalog screens
need data, so they are checked with whatever catalog the caller provides.
"""

from tee_concierge.application.engine import catalog_nodes
from tee_concierge.application.engine.nav import MAIN
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import decode
from tee_concierge.application.menu.builder import Menu
from tee_concierge.domain.catalog import Category, Product, Variant
from tee_concierge.domain.ports import CatalogRepository

_CATALOG_INTERNALS = {
    catalog_nodes.CATEGORY,
    catalog_nodes.PRODUCT,
    catalog_nodes.SIZES,
    catalog_nodes.STOCK,
}


class EmptyCatalog:
    """Stand-in when no database is available (e.g. `tee-menu validate`)."""

    async def list_categories(self) -> list[Category]:
        return []

    async def get_category(self, category_id: int) -> Category | None:
        return None

    async def list_products(
        self, category_id: int, offset: int, limit: int
    ) -> tuple[list[Product], int]:
        return [], 0

    async def get_product(self, product_id: int) -> Product | None:
        return None

    async def list_variants(self, product_id: int) -> list[Variant]:
        return []


async def dry_run(menu: Menu, catalog: CatalogRepository | None = None) -> list[str]:
    """Returns every problem found; an empty list means all reachable screens render."""
    catalog = catalog or EmptyCatalog()
    errors: list[str] = []
    pending, seen, reached = ["go:main"], set[str](), set[str]()
    while pending:
        option_id = pending.pop()
        if option_id in seen:
            continue
        seen.add(option_id)
        route = decode(option_id)
        node = menu.registry.get(route.node) if route else None
        if route is None or node is None:
            errors.append(f"link to missing node: {option_id}")
            continue
        reached.add(node.id)
        ctx = NodeContext(
            menu.business, catalog, menu.messages, menu.nav, route.args, profile_name="Cliente"
        )
        try:
            reply = await node.handler(ctx)
        except (ValueError, KeyError, TypeError) as error:
            errors.append(f"screen '{node.id}' cannot be rendered: {error}")
            continue
        if not reply.options:
            errors.append(f"screen '{node.id}' is a dead end (no options)")
        if node.id != MAIN and MAIN not in {r.node for o in reply.options if (r := decode(o.id))}:
            errors.append(f"screen '{node.id}' has no way back to the main menu")
        pending.extend(o.id for o in reply.options)
    orphans = {n.id for n in menu.registry} - reached - _CATALOG_INTERNALS
    errors.extend(
        f"node '{node_id}' is unreachable from the main menu" for node_id in sorted(orphans)
    )
    return errors
