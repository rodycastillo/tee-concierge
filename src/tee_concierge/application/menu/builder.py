"""Turns a validated menu config into the node registry the engine runs on."""

from dataclasses import dataclass

from tee_concierge.application.content.messages import Messages, fill
from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine import catalog_nodes
from tee_concierge.application.engine.nav import MAIN, go, navigation
from tee_concierge.application.engine.nodes import (
    NavTargets,
    Node,
    NodeContext,
    NodeHandler,
    NodeRegistry,
)
from tee_concierge.application.menu.config import (
    BusinessConfig,
    CatalogNode,
    ContactNode,
    MenuConfig,
    MenuNode,
    NodeConfig,
    TextNode,
)
from tee_concierge.application.menu.validation import (
    MAIN_CODE,
    check_config,
    iter_nodes,
    resolve_codes,
)
from tee_concierge.domain.messaging import Option, Reply


class MenuConfigError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("invalid menu config:\n- " + "\n- ".join(errors))
        self.errors = errors


@dataclass(frozen=True, slots=True)
class Menu:
    registry: NodeRegistry
    nav: NavTargets
    messages: Messages
    business: StoreInfo


def business_info(config: BusinessConfig) -> StoreInfo:
    return StoreInfo(name=config.name, contact_phone=config.contact_phone, hours=config.hours)


def _values(ctx: NodeContext) -> dict[str, object]:
    return {
        "business": ctx.business.name,
        "hours": ctx.business.hours or "",
        "phone": ctx.business.contact_phone,
        "link": ctx.business.whatsapp_link or "",
    }


def build_menu(config: MenuConfig) -> Menu:
    errors = check_config(config)
    if errors:
        raise MenuConfigError(errors)
    messages = Messages.with_overrides(config.messages)
    business = business_info(config.business)
    codes = resolve_codes(config)
    show_codes = config.business.show_codes

    def option(node: NodeConfig) -> Option:
        title = f"{codes[node.id]} {node.title}" if show_codes else node.title
        return Option(go(node.id, "").id, title)

    nodes = list(iter_nodes(config.menu))
    nav = NavTargets(
        contact=next((n.id for n, _p, _a in nodes if isinstance(n, ContactNode)), None),
        catalog=next((n.id for n, _p, _a in nodes if isinstance(n, CatalogNode)), None),
    )

    def text_handler(node: TextNode, parent: str) -> NodeHandler:
        async def handler(ctx: NodeContext) -> Reply:
            return Reply(
                fill(node.body, **_values(ctx)), navigation(ctx, parent), image_url=node.image_url
            )

        return handler

    def contact_handler(node: ContactNode) -> NodeHandler:
        async def handler(ctx: NodeContext) -> Reply:
            if not ctx.business.contact_phone:
                return Reply(ctx.messages.contact_missing, (go(MAIN, ctx.messages.label_main),))
            template = node.body or ctx.messages.contact
            return Reply(fill(template, **_values(ctx)), (go(MAIN, ctx.messages.label_main),))

        return handler

    def menu_handler(node: MenuNode, parent: str) -> NodeHandler:
        async def handler(ctx: NodeContext) -> Reply:
            options = tuple(option(child) for child in node.children) + navigation(ctx, parent)
            return Reply(fill(node.body, **_values(ctx)), options)

        return handler

    async def main_handler(ctx: NodeContext) -> Reply:
        first = ctx.profile_name.split()[0][:30] if ctx.profile_name else None
        template = ctx.messages.welcome_named if first else ctx.messages.welcome
        body = fill(template, name=first or "", **_values(ctx))
        return Reply(
            body, tuple(option(n) for n in config.menu), list_button=ctx.messages.list_button
        )

    registry = NodeRegistry()
    for node, parent, _auto in nodes:
        handler: NodeHandler
        if isinstance(node, TextNode):
            handler = text_handler(node, parent)
        elif isinstance(node, ContactNode):
            handler = contact_handler(node)
        elif isinstance(node, CatalogNode):
            handler = catalog_nodes.catalog
        else:
            handler = menu_handler(node, parent)
        registry.register(Node(node.id, parent, handler, codes[node.id], tuple(node.keywords)))
    if nav.catalog:
        registry.register(Node(catalog_nodes.CATEGORY, nav.catalog, catalog_nodes.category))
        registry.register(Node(catalog_nodes.PRODUCT, nav.catalog, catalog_nodes.product))
        registry.register(Node(catalog_nodes.SIZES, nav.catalog, catalog_nodes.sizes))
        registry.register(Node(catalog_nodes.STOCK, nav.catalog, catalog_nodes.stock))
    # Registered last so that specific keywords win over greetings.
    registry.register(
        Node(MAIN, None, main_handler, MAIN_CODE, tuple(config.business.greeting_keywords))
    )
    return Menu(registry, nav, messages, business)
